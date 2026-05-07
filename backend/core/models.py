"""核心数据模型 - Pydantic"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from enum import Enum
from uuid import uuid4


def uid() -> str:
    return uuid4().hex[:12]


class StoryGenre(str, Enum):
    XIANXIA = "仙侠"
    XUANHUAN = "玄幻"
    DUSHI = "都市"
    YANQING = "言情"
    XUANYI = "悬疑"
    KEHUAN = "科幻"
    LISHI = "历史"
    WUXIA = "武侠"
    YOUXI = "游戏"
    QIHUAN = "奇幻"
    OTHER = "其他"


class StoryStyle(str, Enum):
    QINGSONG = "轻松幽默"
    YANSU = "严肃文学"
    SHUANGLANG = "爽文快节奏"
    WENQING = "文青细腻"
    XUANYIJINTONG = "悬疑紧绷"
    REXIE = "热血战斗"
    NUEWEN = "虐心催泪"
    TIANCHONG = "甜宠治愈"


class NarrativePOV(str, Enum):
    FIRST_PERSON = "第一人称"
    THIRD_PERSON_LIMITED = "第三人称有限"
    THIRD_PERSON_OMNISCIENT = "第三人称全知"


class ChapterStatus(str, Enum):
    DRAFT = "draft"
    CHECKING = "checking"
    REWRITING = "rewriting"
    ACCEPTED = "accepted"
    PUBLISHED = "published"


# --- Story Level ---

class StyleVector(BaseModel):
    """风格量化向量"""
    avg_sentence_length: float = 18.0
    dialogue_ratio: float = 0.35
    metaphor_density: float = 0.05  # 每百句比喻数
    adverb_ratio: float = 0.03
    paragraph_length_median: int = 4
    perspective_consistency: float = 1.0


class WorldBible(BaseModel):
    """世界观圣经"""
    setting: str = ""           # 世界观设定
    rules: list[str] = []       # 世界规则（不可打破）
    factions: list[str] = []    # 势力
    timeline: dict[str, str] = {}  # {事件: 章节}


class StoryConfig(BaseModel):
    """故事创建配置"""
    title: str
    genre: StoryGenre
    style: StoryStyle
    pov: NarrativePOV = NarrativePOV.THIRD_PERSON_LIMITED
    target_chapters: int = 50
    words_per_chapter: int = 3000
    target_audience: str = "大众读者"
    theme: str = ""
    style_vector: StyleVector = StyleVector()


class Story(BaseModel):
    """故事运行时状态"""
    id: str = Field(default_factory=uid)
    config: StoryConfig
    outline: list[dict] = []         # [{chapter, goal, plot_points, emotional_beat}]
    world_bible: WorldBible = WorldBible()
    characters: list[dict] = []      # [{name, role, traits, arc, status}]
    foreshadowing_list: list[dict] = []  # ForeshadowingItem
    current_chapter: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "drafting"


# --- Chapter Level ---

class ForeshadowingItem(BaseModel):
    id: str = Field(default_factory=uid)
    planted_chapter: int
    description: str
    payoff_chapter: Optional[int] = None
    status: str = "unresolved"  # unresolved, resolved, abandoned
    min_payoff_chapter: Optional[int] = None
    max_payoff_chapter: Optional[int] = None


class EmotionSample(BaseModel):
    """情感采样点"""
    chapter: int
    position_pct: float  # 0.0-1.0 在章节中的位置
    tension: float       # 0-10 紧张
    relaxation: float    # 0-10 放松
    sadness: float       # 0-10 悲伤
    pleasure: float      # 0-10 愉悦


class QualityScores(BaseModel):
    """多维度质量评分 (0-10)"""
    coherence: float = 7.0      # 一致性：L1+L2+L3 综合
    originality: float = 7.0    # 原创性
    alignment: float = 7.0      # 大纲对齐
    emotion: float = 7.0        # 情感曲线匹配
    style: float = 7.0          # 风格匹配
    overall: float = 7.0        # 加权总分

    def min_dimension(self) -> float:
        return min(self.coherence, self.originality, self.alignment, self.emotion, self.style)


class CheckResult(BaseModel):
    """质量检查结果"""
    passed: bool
    layer: str  # L1/L2/L3/quality/multi_dim
    issues: list[dict] = []  # [{location, type, description, severity}]
    scores: dict = {}
    quality_scores: Optional[QualityScores] = None  # 多维度评分（multi_dim检查时填充）


class ChapterRecord(BaseModel):
    """章节记录"""
    id: str = Field(default_factory=uid)
    story_id: str
    chapter_number: int
    title: str = ""
    content: str = ""
    summary: str = ""
    word_count: int = 0
    status: ChapterStatus = ChapterStatus.DRAFT
    emotion_curve: list[EmotionSample] = []
    check_results: list[CheckResult] = []
    alignment_score: float = 0.0
    originality_score: float = 0.0
    rewrites_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = ""
    foreshadowing_planted: list[str] = []  # foreshadowing IDs
    foreshadowing_resolved: list[str] = []


# --- Memory Models ---

class HotMemory(BaseModel):
    """热记忆：最近N章全文 + 当前大纲"""
    recent_chapters: list[dict] = []  # [{number, content}]
    current_outline: dict = {}


class WarmMemory(BaseModel):
    """温记忆：角色状态 + 伏笔状态 + 近期摘要"""
    character_states: dict[str, dict] = {}  # {name: {last_known, emotional_state, location}}
    active_foreshadowing: list[dict] = []
    recent_summaries: list[dict] = []  # [{chapter, summary}]


class ColdMemory(BaseModel):
    """冷记忆：世界观 + 风格配置 + 角色卡"""
    world_bible: WorldBible = WorldBible()
    style_config: StyleVector = StyleVector()
    character_cards: list[dict] = []
