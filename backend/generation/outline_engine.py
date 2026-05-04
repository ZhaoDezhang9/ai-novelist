"""大纲引擎 - 生成小说大纲、世界观、角色"""
import json
import re
import logging
from backend.core.models import Story, WorldBible, StyleVector
from backend.core.llm_client import main_llm
from backend.core.utils import extract_json
from backend.generation.prompt_templates import (
    outline_system_prompt, outline_user_prompt,
    world_bible_system_prompt, character_system_prompt,
    STYLE_VECTORS,
)


logger = logging.getLogger(__name__)


class OutlineEngine:
    def __init__(self):
        pass

    async def generate(self, story: Story) -> list[dict]:
        """生成完整大纲"""
        system = outline_system_prompt(story)
        user = outline_user_prompt(story)

        raw = await main_llm.chat(system, user, temperature=0.9, max_tokens=16000)
        outline = self._parse_outline(raw, story.config.target_chapters)

        # 注入转折点
        outline = self._inject_twists(outline, story.config.genre.value)

        # 确保三幕结构
        outline = self._ensure_three_acts(outline)

        return outline

    async def generate_world_bible(self, story: Story) -> WorldBible:
        """生成世界观圣经"""
        system = world_bible_system_prompt(story)
        user = f"请为{story.config.genre}小说《{story.config.title}》构建世界观。"

        raw = await main_llm.chat(system, user, temperature=0.8, max_tokens=4000)
        return self._parse_world_bible(raw)

    async def generate_characters(self, story: Story) -> list[dict]:
        """生成角色设定"""
        system = character_system_prompt(story)
        user = f"请为{story.config.genre}小说《{story.config.title}》设计主要角色阵容。"

        raw = await main_llm.chat(system, user, temperature=0.85, max_tokens=8000)
        try:
            data = json.loads(extract_json(raw))
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        return v
                return [data]
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            logger.warning(f"解析角色数据失败: {e}")
            return [{"name": "主角", "role": "主角", "traits": "待定", "arc": "待定"}]

    def _parse_outline(self, raw: str, target_count: int) -> list[dict]:
        """解析LLM返回的大纲"""
        try:
            data = json.loads(extract_json(raw))
            if isinstance(data, list):
                return data[:target_count]
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"解析大纲JSON失败，使用回退解析: {e}")

        # 手动解析回退
        results = []
        chapters = re.split(r'\n(?=第?\d+[章節])', raw)
        for i, ch in enumerate(chapters, 1):
            if i > target_count:
                break
            results.append({
                "chapter": i,
                "title": f"第{i}章",
                "goal": ch.strip()[:100] if ch.strip() else "推进剧情",
                "plot_points": [ch.strip()[:50]] if ch.strip() else [],
                "emotional_beat": "中性",
                "key_characters": [],
                "foreshadowing_seeds": [],
                "twist_note": "",
            })
        return results or [{"chapter": i, "title": f"第{i}章", "goal": "推进剧情", "plot_points": [], "emotional_beat": "中性", "key_characters": [], "foreshadowing_seeds": [], "twist_note": ""} for i in range(1, target_count + 1)]

    def _parse_world_bible(self, raw: str) -> WorldBible:
        try:
            data = json.loads(extract_json(raw))
            if isinstance(data, list):
                data = data[0] if data else {}
            return WorldBible(
                setting=data.get("setting", ""),
                rules=data.get("rules", []),
                factions=data.get("factions", []),
                timeline=data.get("timeline", {}),
            )
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            logger.warning(f"解析世界观数据失败: {e}")
            return WorldBible(setting=raw[:500])

    def _ensure_three_acts(self, outline: list[dict]) -> list[dict]:
        """确保三幕结构标注"""
        total = len(outline)
        act1_end = total // 3
        act2_end = total * 2 // 3

        for i, item in enumerate(outline):
            if i == 0:
                item["act"] = "第一幕-开端"
            elif i == act1_end:
                item["act"] = "第一幕-结束"
            elif i == act1_end + 1:
                item["act"] = "第二幕-开端"
            elif i == act2_end:
                item["act"] = "第二幕-结束"
            elif i == act2_end + 1:
                item["act"] = "第三幕-开端"
            elif i == total - 1:
                item["act"] = "第三幕-终章"

        return outline

    def _inject_twists(self, outline: list[dict], genre: str) -> list[dict]:
        """注入转折点"""
        from backend.generation.prompt_templates import TWIST_PATTERNS

        twists = TWIST_PATTERNS.get(genre, TWIST_PATTERNS.get("玄幻", []))
        if not twists:
            return outline

        total = len(outline)
        # 每10章插入一个转折
        twist_positions = range(0, total, max(1, total // max(1, len(twists))))
        twist_idx = 0
        for i, pos in enumerate(twist_positions):
            if pos < total and twist_idx < len(twists):
                if not outline[pos].get("twist_note"):
                    outline[pos]["twist_note"] = twists[twist_idx]
                twist_idx += 1

        return outline
