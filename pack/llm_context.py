import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Union

from .llm_fetcher import LLMFetcher


@dataclass
class LLMContext:
    """One chat message."""
    role: str
    content: str
    tool_call_id: Optional[str] = None

    def to_dict(self) -> Dict[str, str]:
        d: Dict[str, str] = {
            "role": self.role,
            "content": self.content
        }
        if self.tool_call_id:
            d["tool_call_id"] = self.tool_call_id
        return d

@dataclass
class LLMContextPair:
    context_in: LLMContext
    context_out: LLMContext

    def to_dict(self) -> Dict[str, LLMContext]:
        return {
            "context_in": self.context_in,
            "context_out": self.context_out
        }


@dataclass
class LLMContextCompressed:
    abstract_msg: str
    source: List[LLMContextPair]

    def to_dict(self) -> Dict[str, Union[str, List[LLMContextPair]]]:
        return {
            "abstract_msg": self.abstract_msg,
            "source": self.source
        }


LLMInfo = Union[LLMContextPair, LLMContextCompressed]

class LLMContextHandler:
    """
    用于处理 LLM 上下文内容的管理器，对每一个 agent 都要有一个实例。
    """
    def __init__(
        self,
        llm_handler: LLMFetcher,
        fallback_order: Optional[List[str]] = None
    ):
        """
        初始化。

        Args:
            llm_handler: 传入的 LLM 实例内容。
            fallback_order: 可选的回退后端顺序列表。
        """
        self.llm_handler = llm_handler
        self.fallback_order = fallback_order

        # 用于保存
        self.context_dict: Dict[int, LLMInfo] = {}

        # ID
        self.now_context_id: int = 0

    async def add_context(
        self,
        context_pair: LLMContextPair
    ):
        """
        加入上下文内容。
        对于一个 Agent 而言，需要保存的信息里可不包含系统提示词。
    
        Args:
            context_pair: 被加入的“输入-输出”上下文。
        """
        self.context_dict[self.now_context_id] = context_pair
        self.now_context_id += 1
    
    async def get_now_context(self) -> List[Dict[str, str]]:
        """
        获取当前上下文，以消息字典列表格式。

        Returns:
            按顺序排列的消息字典列表，每个字典包含 "role" 和 "content" 键。
        """
        if not self.context_dict:
            return []

        messages: List[Dict[str, str]] = []
        for entry in self.context_dict.values():
            # 对于原始 IO 对
            if isinstance(entry, LLMContextPair):
                messages.append({"role": "user", "content": entry.context_in.content})
                messages.append({"role": "assistant", "content": entry.context_out.content})
            # 对于被压缩后的上下文信息
            elif isinstance(entry, LLMContextCompressed):
                messages.append({"role": "assistant", "content": entry.abstract_msg})

        return messages
    
    async def get_now_context_as_single_str(self) -> str:
        """
        获取当前上下文，以单个字符串格式。每行一条内容。
        """
        messages = await self.get_now_context()
        lines: List[str] = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "user":
                lines.append(f"[User]: {content}")
            elif role == "assistant":
                lines.append(f"[Assistant]: {content}")
            else:
                lines.append(f"[{role.capitalize()}]: {content}")
        return "\n".join(lines)
    
    async def compress_context(self, id_list: Optional[List[int]] = None) -> bool:
        """
        压缩当前全部上下文，或者给定压缩索引，将其压缩。
        """
        if not self.context_dict:
            return False

        # 获取当前上下文内容，并将其转为文本
        lines = await self.get_now_context_as_single_str()

        prompt = f"请压缩下列上下文内容，保留关键信息：\n\n{lines}"

        # 等待压缩结果。
        response = await self.llm_handler.fetch(msg=prompt, fallback_order=self.fallback_order)
        compressed_text = response.choices[0].message.content or ""

        # 创建索引结果，然后用压缩后的结果，替代当前的内容。
        source_pairs: List[LLMContextPair] = [
            entry for entry in self.context_dict.values()
            if isinstance(entry, LLMContextPair)
        ]

        compressed = LLMContextCompressed(
            abstract_msg=compressed_text,
            source=source_pairs
        )
        self.context_dict = {0: compressed}
        self.now_context_id = 1
        
        return True
    
    async def get_context_by_id(
        self, 
        id_list: List[int]
    ) -> List[LLMInfo]:
        """
        根据上下文 ID，获取上下文内容。
        """
        return [self.context_dict[i] for i in id_list if i in self.context_dict]
    
    async def generate_memory(self, id_list: List[int]) -> Optional[str]:
        """
        将特定的上下文内容提取为短条内容。
        - 这是作为“记忆“的重要部分，记忆不会被格式化。
        """
        if not self.context_dict:
            return None
        
        entries = await self.get_context_by_id(id_list)
        if not entries:
            return None

        lines = await self.get_now_context_as_single_str()

        prompt = f"请将下列对话内容总结为一条记忆摘要，保留关键信息：\n\n{lines}"

        response = await self.llm_handler.fetch(msg=prompt, fallback_order=self.fallback_order)
        return response.choices[0].message.content or None