"""分层记忆系统 - 热/温/冷三级记忆，替代全文喂入"""
import json
import logging
from typing import Optional

from backend.core.models import (
    Story, ChapterRecord, HotMemory, WarmMemory, ColdMemory,
    ForeshadowingItem, WorldBible, StyleVector,
)
from backend.core.config import get_settings
from backend.core.llm_client import fast_llm
from backend.core.utils import extract_json
from backend.memory import story_db


logger = logging.getLogger(__name__)


class TieredMemory:
    """三级记忆管理器"""

    def __init__(self):
        self.settings = get_settings()
        self.story: Optional[Story] = None
        self._summary_cache: dict[str, str] = {}
        self._char_states_cache: dict = {}

    def set_story(self, story: Story):
        """初始化/切换故事"""
        self.story = story
        self._summary_cache.clear()
        self._char_states_cache.clear()

    async def get_hot(self, chapter_number: int) -> HotMemory:
        """热记忆：最近N章全文 + 当前大纲节点"""
        recent = []
        start = max(1, chapter_number - self.settings.hot_chapters)
        for n in range(start, chapter_number):
            ch_data = await story_db.load_chapter(self.story.id, n) if self.story else None
            content = ch_data.get("content", "") if ch_data else ""
            summary = ch_data.get("summary", "") if ch_data else ""
            recent.append({"number": n, "content": content, "summary": summary})

        current_outline = {}
        if self.story and self.story.outline:
            idx = chapter_number - 1
            if 0 <= idx < len(self.story.outline):
                current_outline = self.story.outline[idx]

        return HotMemory(
            recent_chapters=recent,
            current_outline=current_outline,
        )

    def get_warm(self) -> WarmMemory:
        """温记忆：角色状态 + 活跃伏笔 + 近期摘要"""
        char_states = self._char_states_cache or {}
        active_fs = []
        if self.story:
            active_fs = [
                item for item in self.story.foreshadowing_list
                if isinstance(item, dict) and item.get("status") == "unresolved"
            ]
            if not active_fs:
                active_fs = self.story.foreshadowing_list

        recent_summaries = [
            {"chapter": k.split("_")[-1], "summary": v}
            for k, v in self._summary_cache.items()
        ][-self.settings.warm_summary_chapters:]

        return WarmMemory(
            character_states=char_states,
            active_foreshadowing=active_fs,
            recent_summaries=recent_summaries,
        )

    def get_cold(self) -> ColdMemory:
        """冷记忆：世界观 + 风格 + 角色卡"""
        return ColdMemory(
            world_bible=self.story.world_bible if self.story else WorldBible(),
            style_config=self.story.config.style_vector if self.story else StyleVector(),
            character_cards=self.story.characters if self.story else [],
        )

    async def update_after_chapter(self, chapter: ChapterRecord):
        """章节通过后更新记忆"""
        if self.story:
            try:
                summary = await self._summarize_chapter(chapter)
                self._summary_cache[f"ch_{chapter.chapter_number}"] = summary
            except Exception as e:
                logger.warning(f"生成章节摘要失败: {e}")

        if self.story and chapter.content:
            try:
                states = await self._update_character_states(chapter)
                self._char_states_cache.update(states)
            except Exception as e:
                logger.warning(f"更新角色状态失败: {e}")

    async def _summarize_chapter(self, chapter: ChapterRecord) -> str:
        """用轻量模型生成章节摘要"""
        content = chapter.content[:2000]
        if not content.strip():
            return ""
        prompt = f"请用2-3句话（不超过150字）总结以下小说章节的核心情节：\n\n{content}"
        try:
            result = await fast_llm.chat("你是小说编辑，负责总结章节内容。", prompt, temperature=0.3, max_tokens=300)
            return result.strip()
        except Exception as e:
            logger.warning(f"调用LLM生成摘要失败: {e}")
            return ""

    async def _update_character_states(self, chapter: ChapterRecord) -> dict:
        """从章节文本提取角色当前状态"""
        if not self.story or not self.story.characters:
            return {}
        names = [c.get("name", "") for c in self.story.characters[:5] if c.get("name")]
        if not names:
            return {}

        content = chapter.content[:3000]
        names_str = "、".join(names)
        prompt = (
            f"以下是一章小说内容，请提取每个角色的当前状态。\n"
            f"角色列表：{names_str}\n"
            f"对每个角色输出JSON格式：{{\"角色名\": {{\"location\": \"位置\", \"emotion\": \"情绪\", \"goal\": \"当前目标\"}}}}\n\n{content}"
        )
        try:
            raw = await fast_llm.chat(
                "你是角色状态追踪师，从章节中提取角色状态。只输出JSON格式。",
                prompt, temperature=0.2, max_tokens=800,
            )
            data = json.loads(extract_json(raw))
            if isinstance(data, dict):
                return data
            return {}
        except Exception as e:
            logger.warning(f"提取角色状态失败: {e}")
            return {}
