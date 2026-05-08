"""大纲引擎 - 生成小说大纲、世界观、角色"""
import json
import re
import logging
from backend.core.models import Story, WorldBible
from backend.core.llm_client import planning_llm
from backend.core.utils import parse_llm_json
from backend.generation.prompt_templates import (
    outline_system_prompt, outline_user_prompt,
    world_bible_system_prompt, character_system_prompt,
)


logger = logging.getLogger(__name__)


class OutlineEngine:
    def __init__(self):
        pass

    async def generate(self, story: Story) -> list[dict]:
        """生成完整大纲（使用planning模型降低成本）"""
        system = outline_system_prompt(story)
        user = outline_user_prompt(story)

        raw = await planning_llm.chat(system, user, temperature=0.9, max_tokens=16000)
        outline = self._parse_outline(raw, story.config.target_chapters)

        # 注入转折点
        outline = self._inject_twists(outline, story.config.genre.value)

        # 确保三幕结构
        outline = self._ensure_three_acts(outline)

        return outline

    async def generate_world_bible(self, story: Story) -> WorldBible:
        """生成世界观圣经（使用planning模型降低成本）"""
        system = world_bible_system_prompt(story)
        user = f"请为{story.config.genre}小说《{story.config.title}》构建世界观。"

        raw = await planning_llm.chat(system, user, temperature=0.8, max_tokens=4000)
        return self._parse_world_bible(raw)

    async def generate_characters(self, story: Story) -> list[dict]:
        """生成角色设定（使用planning模型降低成本）"""
        system = character_system_prompt(story)
        user = f"请为{story.config.genre}小说《{story.config.title}》设计主要角色阵容。"

        raw = await planning_llm.chat(system, user, temperature=0.85, max_tokens=8000)
        try:
            data = parse_llm_json(raw)
            if isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        return [x for x in v if isinstance(x, dict)]
                return [data]
            if isinstance(data, list):
                return [x for x in data if isinstance(x, dict)]
            return []
        except (json.JSONDecodeError, IndexError, AttributeError, ValueError) as e:
            logger.warning(f"解析角色数据失败: {e}")
            return [{"name": "主角", "role": "主角", "traits": "待定", "arc": "待定"}]

    def _parse_outline(self, raw: str, target_count: int) -> list[dict]:
        """解析LLM返回的大纲"""
        try:
            data = parse_llm_json(raw)
            if isinstance(data, list):
                return data[:target_count]
            if isinstance(data, dict):
                # LLM 可能返回 {"chapters": [...]} 或 {"outline": [...]}
                for key in ("chapters", "outline", "data"):
                    if key in data and isinstance(data[key], list):
                        return data[key][:target_count]
                # 或者返回 {1: {...}, 2: {...}} 按数字键
                items: list[dict] = []
                for k, v in sorted(data.items()):
                    if isinstance(v, dict):
                        v["chapter"] = v.get("chapter", len(items) + 1)
                        items.append(v)
                if items:
                    return items[:target_count]
        except (json.JSONDecodeError, ValueError) as e:
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
            data = parse_llm_json(raw)
            if isinstance(data, list):
                data = data[0] if data else {}
            # 规范化 rules: LLM 可能返回 [{"rule": "..."}] 或 ["..."]
            rules = []
            for r in data.get("rules", []):
                if isinstance(r, dict):
                    rules.append(r.get("rule", r.get("description", str(r))))
                else:
                    rules.append(str(r))
            # 规范化 factions: LLM 可能返回 [{"name": "...", "description": "..."}] 或 ["..."]
            factions = []
            for f in data.get("factions", []):
                if isinstance(f, dict):
                    name = f.get("name", "")
                    desc = f.get("description", "")
                    factions.append(f"{name}：{desc}" if desc else name)
                else:
                    factions.append(str(f))
            # 规范化 timeline: LLM 可能返回 [{"event": "...", "time": "..."}] 列表
            timeline = data.get("timeline", {})
            if isinstance(timeline, list):
                tl_dict = {}
                for t in timeline:
                    if isinstance(t, dict):
                        event = t.get("event", t.get("description", str(t)))
                        tl_dict[event] = t.get("time", t.get("date", "未知"))
                    else:
                        tl_dict[str(t)] = "未知"
                timeline = tl_dict
            if not isinstance(timeline, dict):
                timeline = {}
            return WorldBible(
                setting=data.get("setting", ""),
                rules=rules,
                factions=factions,
                timeline=timeline,
            )
        except (json.JSONDecodeError, IndexError, AttributeError, ValueError) as e:
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
