"""伏笔管理器 - 埋设/追踪/回收/逾期提醒"""
import json
from backend.core.models import Story, ChapterRecord, ForeshadowingItem
from backend.core.llm_client import fast_llm
from backend.core.utils import extract_json


class ForeshadowingManager:
    def __init__(self):
        self._check_interval = 3

    async def update_after_chapter(self, story: Story, chapter: ChapterRecord):
        """章节入库后更新伏笔状态（传统方式，两次调用）"""
        ch_num = chapter.chapter_number
        changes = []

        new_fs = await self._detect_new_foreshadowing(story, chapter)
        for fs in new_fs:
            story.foreshadowing_list.append(fs.model_dump())
            chapter.foreshadowing_planted.append(fs.id)
            changes.append(f"第{ch_num}章埋下伏笔：{fs.description[:30]}")

        resolved = await self._detect_resolved_foreshadowing(story, chapter)
        for fs_id in resolved:
            for item in story.foreshadowing_list:
                if isinstance(item, dict) and item.get("id") == fs_id:
                    item["status"] = "resolved"
                    item["payoff_chapter"] = ch_num
                    chapter.foreshadowing_resolved.append(fs_id)

        if ch_num % self._check_interval == 0:
            overdue = self._get_overdue(story, ch_num)
            if overdue:
                for item in story.foreshadowing_list:
                    if isinstance(item, dict) and item.get("id") in overdue:
                        item["status_alert"] = "overdue"

    async def update_after_chapter_combined(self, story: Story, chapter: ChapterRecord):
        """合并新伏笔检测+已回收伏笔检测为一次LLM调用"""
        ch_num = chapter.chapter_number
        content = chapter.content[:3000]
        if not content.strip():
            return

        chars = [c.get("name", "") for c in story.characters if c.get("name")]
        chars_str = "、".join(chars[:5]) if chars else "主角"

        active = [
            item for item in story.foreshadowing_list
            if isinstance(item, dict) and item.get("status") == "unresolved"
        ]
        active_desc = "\n".join([
            f"ID:{item.get('id','?')} | 第{item.get('planted_chapter','?')}章 | {item.get('description','')}"
            for item in active
        ]) if active else "无活跃伏笔"

        prompt = (
            f"请同时完成两项伏笔检测任务：\n\n"
            f"任务1：检测本章新埋的伏笔（悬念、未解之谜、暗示）\n"
            f"任务2：判断以下未回收伏笔是否在本章被回收\n\n"
            f"当前角色：{chars_str}\n\n"
            f"【未回收伏笔】\n{active_desc}\n\n"
            f"【本章内容】\n{content}\n\n"
            f'输出JSON格式：{{"new_foreshadowing": [{{"description": "伏笔描述", "min_payoff_chapter": 最早回收章或无0}}], "resolved_ids": ["被回收的伏笔ID"]}}\n'
            f"注意：没有则输出空数组 []"
        )

        try:
            raw = await fast_llm.chat(
                "你是伏笔分析师，检测新伏笔和已回收伏笔。只输出JSON。",
                prompt, temperature=0.3, max_tokens=800,
            )
            data = json.loads(extract_json(raw))

            new_items = data.get("new_foreshadowing", []) if isinstance(data, dict) else []
            for item in new_items:
                fs = ForeshadowingItem(
                    planted_chapter=ch_num,
                    description=item.get("description", "未知伏笔"),
                    min_payoff_chapter=item.get("min_payoff_chapter") or None,
                    status="unresolved",
                )
                story.foreshadowing_list.append(fs.model_dump())
                chapter.foreshadowing_planted.append(fs.id)

            resolved_ids = data.get("resolved_ids", []) if isinstance(data, dict) else []
            for fs_id in resolved_ids:
                for item in story.foreshadowing_list:
                    if isinstance(item, dict) and item.get("id") == fs_id:
                        item["status"] = "resolved"
                        item["payoff_chapter"] = ch_num
                        chapter.foreshadowing_resolved.append(fs_id)
        except Exception:
            return

    async def _detect_new_foreshadowing(self, story: Story, chapter: ChapterRecord) -> list[ForeshadowingItem]:
        """检测本章新埋的伏笔"""
        content = chapter.content[:3000]
        if not content.strip():
            return []

        chars = [c.get("name", "") for c in story.characters if c.get("name")]
        chars_str = "、".join(chars[:5]) if chars else "主角"

        prompt = (
            f"请从以下章节内容中检测新埋下的伏笔（悬念、未解之谜、暗示）。\n"
            f"当前角色：{chars_str}\n\n"
            f"输出JSON数组，每个伏笔包含：\n"
            f"- description: 伏笔描述（30字内）\n"
            f"- min_payoff_chapter: 最早第几章回收（如无法确定则填0）\n\n"
            f"如果没有明确的伏笔，输出空数组 []。\n\n"
            f"章节内容：\n{content}"
        )

        try:
            raw = await fast_llm.chat(
                "你是伏笔分析师，从小说章节中检测新埋的伏笔。只输出JSON。",
                prompt, temperature=0.3, max_tokens=800,
            )
            data = json.loads(extract_json(raw))
            results = []
            for item in data if isinstance(data, list) else []:
                results.append(ForeshadowingItem(
                    planted_chapter=chapter.chapter_number,
                    description=item.get("description", "未知伏笔"),
                    min_payoff_chapter=item.get("min_payoff_chapter") or None,
                    status="unresolved",
                ))
            return results
        except Exception:
            return []

    async def _detect_resolved_foreshadowing(self, story: Story, chapter: ChapterRecord) -> list[str]:
        """检测本章回收的伏笔"""
        active = [
            item for item in story.foreshadowing_list
            if isinstance(item, dict) and item.get("status") == "unresolved"
        ]
        if not active:
            return []

        active_desc = "\n".join([
            f"ID:{item.get('id','?')} | 第{item.get('planted_chapter','?')}章 | {item.get('description','')}"
            for item in active
        ])

        prompt = (
            f"以下悬而未决的伏笔是否在本章得到了回收？\n\n"
            f"【未回收伏笔】\n{active_desc}\n\n"
            f"【本章内容】\n{chapter.content[:3000]}\n\n"
            f"请输出被回收的伏笔ID列表（JSON数组）：[\"id1\", \"id2\"]。\n"
            f"如果没有回收任何伏笔，输出 []。"
        )

        try:
            raw = await fast_llm.chat(
                "你是伏笔追踪师，判断哪些伏笔在本章被回收。只输出JSON数组。",
                prompt, temperature=0.2, max_tokens=300,
            )
            data = json.loads(extract_json(raw))
            return [str(x) for x in data] if isinstance(data, list) else []
        except Exception:
            return []

    def _get_overdue(self, story: Story, current_ch: int) -> list[str]:
        """找出逾期未回收的伏笔"""
        overdue = []
        for item in story.foreshadowing_list:
            if isinstance(item, dict) and item.get("status") == "unresolved":
                min_payoff = item.get("min_payoff_chapter", 0)
                planted = item.get("planted_chapter", 0)
                if min_payoff and current_ch > min_payoff:
                    overdue.append(item["id"])
                elif not min_payoff and current_ch - planted > self._check_interval * 2:
                    overdue.append(item["id"])
        return overdue
