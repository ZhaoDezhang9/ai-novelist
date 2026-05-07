"""Agent 抽象接口 — Protocol/ABC 定义，便于测试和替换"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional
from backend.core.models import Story, WorldBible, ChapterRecord, CheckResult, StyleVector


class WorldbuilderAgent(ABC):
    @abstractmethod
    async def build_world(self, story: Story) -> WorldBible:
        """构建世界观圣经"""


class PlotAgent(ABC):
    @abstractmethod
    async def generate_plot(self, story: Story) -> list[dict]:
        """生成大纲（含三幕结构、转折点、章节规划）"""


class CharacterAgent(ABC):
    @abstractmethod
    async def generate_characters(self, story: Story) -> list[dict]:
        """生成角色设定（性格模型、弧光、关系）"""


class ChapterWriterAgent(ABC):
    @abstractmethod
    async def write_draft(self, story: Story, chapter_number: int, context: str,
                          temperature: Optional[float] = None) -> ChapterRecord:
        """写一章完整草稿"""

    @abstractmethod
    async def write_draft_stream(self, story: Story, chapter_number: int, context: str,
                                 temperature: Optional[float] = None) -> AsyncGenerator[dict, None]:
        """流式写章节"""

    @abstractmethod
    def build_context(self, story: Story, hot, warm, cold,
                      semantic_context: dict | None = None) -> str:
        """构建 LLM 上下文提示词（含语义搜索增强）"""

    @abstractmethod
    async def build_semantic_context(self, story: Story, chapter_number: int) -> dict | None:
        """构建语义搜索上下文"""


class CriticAgent(ABC):
    @abstractmethod
    async def review(self, story: Story, chapter: ChapterRecord, hot_memory=None) -> CheckResult:
        """多维度统一质检（单次 LLM 调用）"""

    @abstractmethod
    async def review_parallel(self, story: Story, chapter: ChapterRecord, hot_memory=None,
                              only_layers: Optional[set[str]] = None) -> list[CheckResult]:
        """并行传统质检（L1+L2+L3+原创性+对齐+情感，6次LLM调用）"""

    @abstractmethod
    async def full_review(self, story: Story):
        """每10章全量对齐审核"""


class StyleAgent(ABC):
    @abstractmethod
    def get_preset(self, style_name: str) -> StyleVector:
        """获取预设风格向量"""

    @abstractmethod
    def from_text(self, text: str) -> StyleVector:
        """从文本提取风格向量"""

    @abstractmethod
    def compare(self, target: StyleVector, actual: StyleVector) -> float:
        """比较两个风格向量相似度 (0.0-1.0)"""
