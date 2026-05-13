import asyncio
from dataclasses import dataclass, field
from re import NOFLAG
from typing import List, Dict, Optional, Tuple, Union, Set

from .llm_fetcher import LLMFetcher


LLMContextValue = Union[
    str, 
    Optional[List[str]]
    ]

@dataclass
class LLMContext:
    """One chat message."""
    role: str
    content: str
    tool_call_info: Optional[List[str]] = None  # 调度了什么工具，可选——有可能调度了不止一件工具。
    tool_call_result: Optional[List[str]] = None
    tags: Optional[List[str]] = field(default_factory=list)   # 用于保存本上下文内容的标签。

    def to_dict(self) -> Dict[str, LLMContextValue]:
        d: Dict[str, LLMContextValue] = {
            "role": self.role,
            "content": self.content,
        }

        # schema: 必须保证工具调度的信息和结果信息同时存在。
        if self.tool_call_info:
            d["tool_call_info"] = self.tool_call_info
        if self.tool_call_result:
            d["tool_call_result"] = self.tool_call_result

        if self.tags:
            d["tags"] =  self.tags

        return d


LLMContextCompactedValue = Union[
    str, 
    List[Union[LLMContext, "LLMContextCompacted"]],
    List[int],
    Optional[List[str]]
]

@dataclass
class LLMContextCompacted:
    """
    用于存储对单条 LLM 上下文执行压缩的结果。
    """
    abstract_msg: str   # 压缩（并抽象后的）结论
    source: List[Union[LLMContext, "LLMContextCompacted"]]    # 原始信息源，必要时让 agent 查询该信息源。可以二压。
    source_ids: List[int] # 原始信息源的id
    tags: Optional[List[str]] = field(default_factory=list)   # 用于保存本上下文内容的标签。

    def to_dict(self) -> Dict[str, LLMContextCompactedValue]:
        d: Dict[str, LLMContextCompactedValue] = {
            "abstract_msg": self.abstract_msg,
            "source": self.source,
            "source_ids": self.source_ids
        }
        if self.tags:
            d["tags"] = self.tags
        
        return d

@dataclass
class LLMCompactedContextInfoItem:
    context_id: int
    info: LLMContextCompacted


@dataclass
class LLMUncompactedContextInfoItem:
    context_id: int
    info: LLMContext

@dataclass
class LLMContextInfo:
    compacted_info: List[LLMCompactedContextInfoItem] = field(default_factory=list)
    uncompacted_info: List[LLMUncompactedContextInfoItem] = field(default_factory=list)

# 设计集合类
LLMInfo = Union[LLMContext, LLMContextCompacted]

class LLMContextHandler:
    """
    用于处理 LLM 上下文内容的管理器，对每一个 agent 都要有一个实例。
    
    Notes:
        该类会在创建类 Agent 时自动为其创建，作为类实例。
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

        # 用于保存以调度为单位的内容 - 分流一个压缩后的信息和一个压缩前的信息。
        self.context_raw_dict: Dict[int, LLMInfo] = {}  # 正查信息池
        self.context_raw_dict_reversed: Dict[LLMInfo, int] = {}  # 反查信息池，根据信息，反查 id
        # 理论上，不应该出现两份完全相同的 LLM 信息

        self.context_dict: Dict[int, LLMContext] = {}   # 全部原始 llm 信息
        self.context_dict_uncompacted: Dict[int, LLMContext] = {}   # 未被压缩的信息
        self.context_dict_compacted: Dict[int, LLMContextCompacted] = {}   # 被压缩的信息追


        # 保存一个特定的逆字典 - 根据特定的标签内容，对上下文 id 进行反查。
        self.reverse_tag_dict: Dict[str, Set[int]] = {}

        # ID - 上述信息用于保存内容时，公用同一个ID
        self.now_context_id: int = 0

    async def add_context(
        self,
        context: LLMContext,
    ) -> None:
        """
        加入上下文内容，二选一。
        对于一个 Agent 而言，需要保存的信息里可不包含系统提示词。
    
        Args:
            context: 每次调度的信息。
        """
        # 维护一个正查和一个反查表。
        self.context_raw_dict[self.now_context_id] = context
        self.context_raw_dict_reversed[context] = self.now_context_id
        

        self.context_dict[self.now_context_id] = context
        self.context_dict_uncompacted[self.now_context_id] = context    # 同时维护一个未压缩的东西

        # 时间线记录，并自增。
        self.now_context_id += 1

        # 如果具有标签，则将标签信息加入索引中
        if context.tags:
            for tag in context.tags:
                # 如果在键里没找到该键，则创建一个
                if tag not in self.reverse_tag_dict.keys():
                    self.reverse_tag_dict[tag] = set()
                # 反查id，并加入
                self.reverse_tag_dict[tag].add(self.context_raw_dict_reversed[context])

    async def get_now_context(
        self, 
        id_list: Optional[List[int]] = None
    ) -> Optional[LLMContextInfo]:
        """
        获取当前上下文，以消息字典列表格式。
        
        Args:
            id_list: 可选返回的上下文内容，如果不填则默认返回全部上下文。

        Returns:
            按顺序排列的消息字典列表。对每一个元素，有如下：
                k: id, v: llminfo
            如果没有上下文内容，返回 None。
        """
        if not self.context_dict:   # 如果上下文字典是空白的
            return None

        compacted_info: List[LLMCompactedContextInfoItem] = []
        uncompacted_info: List[LLMUncompactedContextInfoItem] = []

        # 先将压缩后的内容压进来，注意我需要压入的东西
        for entry_compacted in self.context_dict_compacted.values():
            context_id: int = self.context_raw_dict_reversed[entry_compacted]
            if id_list is not None:
                if context_id in id_list:
                    compacted_info.append(
                        LLMCompactedContextInfoItem(
                            context_id=context_id,
                            info=entry_compacted
                        )
                    )
            else:
                compacted_info.append(
                    LLMCompactedContextInfoItem(
                        context_id=context_id,
                        info=entry_compacted
                    )
                )

        # 再将没压缩的东西压进来
        for entry in self.context_dict_uncompacted.values():
            context_id: int = self.context_raw_dict_reversed[entry]
            if id_list is not None:
                if context_id in id_list:
                    uncompacted_info.append(
                        LLMUncompactedContextInfoItem(
                            context_id=context_id,
                            info=entry
                        )
                    )
            else:
                uncompacted_info.append(
                    LLMUncompactedContextInfoItem(
                        context_id=context_id,
                        info=entry
                    )
                )

        # 根据键进行排序，从小到大进行
        compacted_info.sort(key=lambda x: x.context_id)
        uncompacted_info.sort(key=lambda x: x.context_id)
        
        return LLMContextInfo(
            compacted_info=compacted_info,
            uncompacted_info=uncompacted_info
        )
    
    async def get_now_context_as_single_str(
        self, 
        id_list: Optional[List[int]] = None
    ) -> Optional[str]:
        """
        获取当前上下文，以单个字符串格式。每行一条内容。
        """
        messages: Optional[LLMContextInfo] = await self.get_now_context(id_list)
        if messages == None:
            return None

        compacted_info: List[LLMCompactedContextInfoItem] = messages.compacted_info
        uncompacted_info: List[LLMUncompactedContextInfoItem] = messages.uncompacted_info

        # 接下来需要将这个东西全部序列化了。
        # 已保证过，压缩和未压缩的代码部分，返回的东西都严格保证 schema。
        lines: List[str] = []
        for c_info in compacted_info:
            msg_str: str = f"""
            [COMPACTED ABSTRACT] 
            Abstract info: {c_info.info.abstract_msg}
            This abstract is originally from messages with id: {c_info.context_id}.
            """
            lines.append(msg_str)

            # 这块地方 pyright 会报错，怎么做？
        
        for u_info in uncompacted_info:
            msg_str: str = f"""
            [ROUND]
            Role: {u_info.info.role}
            Content: {u_info.info.content},
            """
            if not u_info.info.tool_call_info:
                msg_str_additional_tool: str = f"""
                This round does not contains any of tool call.
                """
            else:
                msg_str_additional_tool: str = f"""
                Called tools: {u_info.info.tool_call_info},
                Results: {u_info.info.tool_call_result}
                """
            msg_str.join(msg_str_additional_tool)

            lines.append(msg_str)

        return "\n".join(lines)
    
    async def compress_context(self, id_list: Optional[List[int]] = None) -> bool:
        """
        压缩当前全部未压缩上下文，或给定压缩索引，将其压缩。
        TODO: 让 id_list 可用。
        """
        if not self.context_dict:
            return False
        
        # 如果指定了 id，则单独提取并序列化这些。
        # TODO: 需要一个工具函数。

        # 否则，获取当前上下文内容，并将其转为文本
        lines = await self.get_now_context_as_single_str(id_list)

        # 构建上下文内容。
        prompt = f"Please compact the following context, keep essential information:\n\n{lines}"

        # 等待压缩结果。
        response = await self.llm_handler.fetch(msg=prompt, fallback_order=self.fallback_order)
        Compacted_text = response.choices[0].message.content or ""
        
        
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

        prompt = f"Please conclude the folowing conversations into an abstract for memory, \
            keep the essential information:\n\n{lines}"

        response = await self.llm_handler.fetch(msg=prompt, fallback_order=self.fallback_order)
        return response.choices[0].message.content or None
