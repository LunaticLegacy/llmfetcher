"""Native wire payloads, reference persistence and observer byte isolation."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock

from llmfetcher.multimodal import UserMessage, ImageToolResult, bounded_resolver
from llmfetcher.llm_types import LLMBackendConfig, LLMOutput, LLMToolCall
from llmfetcher.llm_fetcher import LLMFetcher
from llmfetcher.context_handlers.linear import ContextHandlerLinear
from llmfetcher.fetcher_handlers.openai import OpenAIHandler
from llmfetcher.fetcher_handlers.anthropic import AnthropicHandler

REF = {'attachment_id': 'img_test', 'media_type': 'image/png', 'detail': 'high'}
DATA = 'c2VjcmV0LWltYWdl'


class NativeVisionTests(unittest.TestCase):
    def context(self):
        context = ContextHandlerLinear(MagicMock())
        context.add_user_message(UserMessage('Inspect', [REF]))
        context.add_assistant_message(LLMOutput('', 'fake', 'fake', 'fake', tool_calls=[
            LLMToolCall('view_image', {}, 'a'), LLMToolCall('other', {}, 'b')]),
            {'a': ImageToolResult('Opened image', [REF]), 'b': 'done'})
        return context

    def handler(self, cls):
        handler = object.__new__(cls)
        handler.fetcher = SimpleNamespace(image_resolver=MagicMock(return_value={
            'media_type': 'image/png', 'data': DATA}))
        handler.backend = LLMBackendConfig('fake', 'openai' if cls is OpenAIHandler else 'anthropic', 'model')
        handler.client = MagicMock()
        return handler

    def test_openai_both_dispatch_modes_and_tool_order(self):
        for streaming in [False, True]:
            handler = self.handler(OpenAIHandler)
            messages = self.context().build_messages()
            handler.create_completion(messages=messages, temperature=0.5, max_tokens=100, stream=streaming)
            wire = handler.client.chat.completions.create.call_args.kwargs['messages']
            self.assertEqual([m['role'] for m in wire], ['user', 'assistant', 'tool', 'tool', 'user'])
            self.assertEqual(wire[0]['content'][1]['image_url']['url'], 'data:image/png;base64,' + DATA)
            self.assertEqual(wire[0]['content'][1]['image_url']['detail'], 'high')
            self.assertEqual(wire[1]['tool_calls'][0]['function']['name'], 'view_image')
            self.assertNotIn(DATA, json.dumps(messages))
            self.assertEqual(messages[0]['images'], [REF])

    def test_anthropic_native_tool_use_and_image_result(self):
        for streaming in [False, True]:
            handler = self.handler(AnthropicHandler)
            handler.create_completion(messages=self.context().build_messages(), temperature=0.5, max_tokens=100, stream=streaming)
            wire = handler.client.messages.create.call_args.kwargs['messages']
            self.assertEqual(wire[0]['content'][1]['source'], {'type': 'base64', 'media_type': 'image/png', 'data': DATA})
            self.assertEqual(wire[1]['content'][0]['type'], 'tool_use')
            self.assertEqual(wire[2]['content'][0]['tool_use_id'], 'a')
            self.assertEqual(wire[2]['content'][0]['content'][1]['type'], 'image')

    def test_checkpoint_and_archive_keep_only_references(self):
        context = self.context()
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'context.json'
            self.assertTrue(context.save(path))
            loaded = ContextHandlerLinear(MagicMock())
            self.assertTrue(loaded.load(path))
            self.assertEqual(loaded.messages[0].images, [REF])
            self.assertEqual(loaded.messages[1].tool_calls[0].images, [REF])
            self.assertEqual(loaded.build_messages(), context.build_messages())
            serialized = json.dumps(context._context_to_dict(context.messages[1]))
            self.assertNotIn(DATA, serialized)
            self.assertEqual(context._context_from_dict(json.loads(serialized)).tool_calls[0].images, [REF])

    def test_preview_never_resolves_bytes_and_rejects_unsupported(self):
        handler = self.handler(OpenAIHandler)
        fetcher = object.__new__(LLMFetcher)
        fetcher._handler_for_backend = lambda backend: handler
        _, snapshot = fetcher._prepare_backend_request(handler.backend, self.context().build_messages(), 0.5, 100, None, False)
        handler.fetcher.image_resolver.assert_not_called()
        self.assertNotIn(DATA, json.dumps(snapshot.to_dict()))
        handler.backend.provider = 'litellm'
        with self.assertRaisesRegex(ValueError, 'does not support'):
            fetcher._prepare_backend_request(handler.backend, self.context().build_messages(), 0.5, 100, None, False)

    def test_validation_missing_resolver_and_request_budget(self):
        with self.assertRaises(ValueError):
            UserMessage('', [{**REF, 'data': DATA}])
        resolver = bounded_resolver(lambda ref: {'media_type': 'image/png', 'data': 'a' * (8 * 1024 * 1024)})
        for _ in range(3):
            resolver(REF)
        with self.assertRaisesRegex(ValueError, '20 MiB'):
            resolver(REF)
        handler = self.handler(OpenAIHandler)
        handler.fetcher.image_resolver = None
        with self.assertRaisesRegex(ValueError, 'image_resolver'):
            handler.create_completion(messages=self.context().build_messages(), temperature=0.5, max_tokens=100, stream=False)
        handler.client.chat.completions.create.assert_not_called()


    def test_image_only_turn_survives_linear_checkpoint(self):
        context = ContextHandlerLinear(MagicMock())
        context.add_user_message(UserMessage('', [REF]))
        with TemporaryDirectory() as directory:
            path = Path(directory) / 'context.json'
            self.assertTrue(context.save(path))
            loaded = ContextHandlerLinear(MagicMock())
            self.assertTrue(loaded.load(path))
            self.assertEqual(loaded.messages[0].images, [REF])
            self.assertEqual(loaded.messages[0].content, '')

    def test_compaction_preview_keeps_marker_never_bytes(self):
        preview = self.context().compaction_request_preview()
        self.assertIn('img_test', preview.text)
        self.assertNotIn(DATA, preview.text)

    def test_graph_handler_preserves_image_references(self):
        from llmfetcher.graph_memory.handler import GraphContextHandler
        handler = GraphContextHandler(
            compacting_fetcher=MagicMock(),
            retrieval_trigger='manual',
        )
        handler.add_user_message(UserMessage('Inspect', [REF]))
        self.assertEqual(handler._pending[0].images, [REF])
        self.assertEqual(handler.linear.messages[0].images, [REF])

    def test_graph_builder_keeps_image_only_turn_reachable(self):
        from llmfetcher.graph_memory.builder import GraphBuilder
        from llmfetcher.graph_memory.graph_store import GraphStore
        from llmfetcher.llm_types import LLMContext
        builder = GraphBuilder(GraphStore(), fetcher=None)
        transcript = builder._render_transcript([
            LLMContext(role='user', timeline=1, content='', images=[REF])
        ])
        self.assertIn('img_test', transcript)
        self.assertNotIn(DATA, transcript)

    def test_archive_retrieval_surfaces_reference_markers(self):
        from llmfetcher.context_handlers.archive_retrieval import retrieve_archive
        from llmfetcher.llm_types import LLMContext
        record = LLMContext(role='user', timeline=2, content='', images=[REF])
        result = retrieve_archive('img_test', [record])
        self.assertTrue(result.evidence)
        self.assertIn('img_test', result.evidence[0].text)
        self.assertNotIn(DATA, result.evidence[0].text)

    def test_retrieved_archival_keeps_reference_markers(self):
        from llmfetcher.context_handlers.retrieved import RetrievedContextHandler
        handler = RetrievedContextHandler(
            tlb_fetcher=MagicMock(),
            compacting_fetcher=MagicMock(),
            retrieval_trigger='manual',
            archive_scope='none',
        )
        handler.add_user_message(UserMessage('Inspect', [REF]))
        text = handler._export_archival_state()
        self.assertIn('img_test', text)
        self.assertNotIn(DATA, text)


if __name__ == '__main__':
    unittest.main()
