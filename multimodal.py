"""Durable image references; bytes exist only during provider dispatch."""
from dataclasses import dataclass, field
from typing import Callable, Literal, NotRequired, TypedDict


class ImageReference(TypedDict):
    attachment_id: str
    media_type: str
    detail: NotRequired[Literal['auto', 'low', 'high']]


ImageResolver = Callable[[ImageReference], dict[str, str]]


def bounded_resolver(resolver):
    """Enforce a per-request decoded-size budget before any network call."""
    total = 0
    count = 0
    def resolve(ref):
        nonlocal total, count
        if resolver is None:
            raise ValueError('Image input requires an image_resolver')
        payload = resolver(ref)
        count += 1
        total += len(payload['data']) * 3 // 4
        if count > 20 or total > 20 * 1024 * 1024:
            raise ValueError('Image request exceeds 20 images or 20 MiB; compact or start a new conversation')
        return payload
    return resolve


def validate_images(images: list[ImageReference]) -> list[ImageReference]:
    """Copy references and reject inline bytes and transport-specific fields."""
    result = []
    for ref in images:
        if set(ref) - {'attachment_id', 'media_type', 'detail'}:
            raise ValueError('Image references may contain only attachment_id, media_type, detail')
        if not isinstance(ref.get('attachment_id'), str) or not ref['attachment_id']:
            raise ValueError('Image attachment_id is required')
        if ref.get('media_type') not in {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}:
            raise ValueError('Unsupported image media_type')
        if ref.get('detail', 'auto') not in {'auto', 'low', 'high'}:
            raise ValueError('Unsupported image detail')
        result.append(dict(ref))
    return result


@dataclass
class UserMessage:
    text: str
    images: list[ImageReference] = field(default_factory=list)

    def __post_init__(self):
        self.images = validate_images(self.images)

    def __str__(self):
        return self.text


@dataclass
class ImageToolResult(UserMessage):
    """Tool feedback containing native image inputs and explanatory text."""


def image_reference_markers(images) -> list[str]:
    """Render bounded, byte-free provenance markers for image references.

    Compaction summaries and archive transcripts must never contain image
    bytes, but an image-only turn also must not vanish without a trace.  A
    text marker keeps each durable reference discoverable so a tool can later
    reopen it by attachment id.
    """
    markers = []
    for ref in images or ():
        if not isinstance(ref, dict):
            continue
        attachment_id = ref.get('attachment_id')
        if not attachment_id:
            continue
        media_type = ref.get('media_type') or 'image/*'
        markers.append(f"[image: {attachment_id} ({media_type})]")
    return markers


def image_blocks(images, resolver, provider):
    """Resolve local references at the wire boundary, never for previews."""
    if not images:
        return []
    if resolver is None:
        raise ValueError('Image input requires an image_resolver')
    blocks = []
    for ref in validate_images(images):
        payload = resolver(ref)
        media_type = payload['media_type']
        if media_type != ref['media_type']:
            raise ValueError('Resolved image MIME does not match reference')
        if provider == 'openai':
            blocks.append({'type': 'image_url', 'image_url': {
                'url': f"data:{media_type};base64,{payload['data']}",
                'detail': ref.get('detail', 'auto'),
            }})
        else:
            blocks.append({'type': 'image', 'source': {
                'type': 'base64', 'media_type': media_type, 'data': payload['data'],
            }})
    return blocks


def openai_image_messages(messages, resolver):
    """Place tool images after all tool replies, preserving protocol ordering."""
    out, pending = [], []
    for original in messages:
        msg = dict(original)
        if msg.get('role') != 'tool' and pending:
            out.append({'role': 'user', 'content': pending})
            pending = []
        images = msg.pop('images', [])
        blocks = image_blocks(images, resolver, 'openai')
        if blocks and msg['role'] == 'tool':
            pending.extend([{'type': 'text', 'text': f"Images from tool call {msg['tool_call_id']}"}, *blocks])
        elif blocks:
            if msg['role'] != 'user':
                raise ValueError('Images require user or tool messages')
            msg['content'] = ([{'type': 'text', 'text': msg['content']}] if msg.get('content') else []) + blocks
        out.append(msg)
    if pending:
        out.append({'role': 'user', 'content': pending})
    return out
