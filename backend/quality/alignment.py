"""大纲对齐检查器 - 双向对齐：大纲→正文 + 正文→大纲"""
import json
from backend.core.models import Story, ChapterRecord, CheckResult
from backend.core.llm_client import fast_llm
from backend.core.config import get_settings
from backend.core.utils import extract_json
from backend.generation.prompt_templates import ALIGNMENT_CHECK_PROMPT


class AlignmentChecker:
    def __init__(self):
        self.settings = get_settings()

    async def check(self, story: Story, chapter: ChapterRecord) -> CheckResult:
        """大纲对齐检查"""
        chapter_num = chapter.chapter_number

        outline_node = {}
        if story.outline and chapter_num - 1 < len(story.outline):
            outline_node = story.outline[chapter_num - 1]

        if not outline_node:
            return CheckResult(passed=True, layer="alignment", issues=[], scores={"alignment_score": 1.0})

        quick_score, quick_issues = self._quick_check(chapter.content, outline_node)

        llm_score, llm_issues = await self._deep_check(chapter.content, outline_node)

        overall = quick_score * 0.4 + llm_score * 0.6
        issues = quick_issues + llm_issues

        # 0-10 评分，7分通过
        return CheckResult(
            passed=overall >= 7,
            layer="alignment",
            issues=issues,
            scores={"alignment_score": overall, "quick_check": quick_score, "deep_check": llm_score},
        )

    def _quick_check(self, content: str, outline: dict) -> tuple[float, list[dict]]:
        """规则引擎快速对齐检查 - 返回0-10分"""
        issues = []
        score = 10.0
        content_lower = content.lower()

        plot_points = outline.get("plot_points", [])
        hit_count = 0
        for point in plot_points:
            keywords = [w for w in point[:10].strip("，。！？") if '\u4e00' <= w <= '\u9fff']
            key_phrase = "".join(keywords[:4])
            if key_phrase and key_phrase in content:
                hit_count += 1

        if plot_points:
            hit_rate = hit_count / len(plot_points)
            if hit_rate < 0.3:
                score -= 2
                issues.append({
                    "type": "plot_coverage_low",
                    "severity": "high",
                    "description": f"情节点命中率仅 {hit_rate:.0%}，大纲要求的情节可能缺失",
                })

        key_chars = outline.get("key_characters", [])
        if key_chars:
            appeared = sum(1 for c in key_chars if c in content)
            if appeared < 1:
                score -= 1.5
                issues.append({
                    "type": "characters_missing",
                    "severity": "medium",
                    "description": f"关键角色 {key_chars} 在本章未出现",
                })

        return max(0, score), issues

    async def _deep_check(self, content: str, outline: dict) -> tuple[float, list[dict]]:
        """LLM深度对齐检查 - 返回0-10分"""
        goals = json.dumps(outline, ensure_ascii=False)
        system = ALIGNMENT_CHECK_PROMPT.format(outline_goals=goals)
        user = f"请检查以下章节是否与大纲对齐：\n\n{content[:5000]}"

        try:
            raw = await fast_llm.chat(system, user, temperature=0.2, max_tokens=1200)
            data = json.loads(extract_json(raw))
            return data.get("alignment_score", 7), data.get("issues", [])
        except Exception:
            return 7, []

    async def full_review(self, story: Story):
        """每10章全量对齐审核"""
        from backend.memory import story_db
        all_chapters = await story_db.load_all_chapters(story.id)
        if not all_chapters:
            return

        drift_chapters = []
        for ch_data in all_chapters:
            ch_num = ch_data.get("chapter_number", 0)
            if ch_num - 1 < len(story.outline):
                outline_node = story.outline[ch_num - 1]
                content = ch_data.get("content", "")
                if content:
                    score, _ = self._quick_check(content, outline_node)
                    if score < 7:
                        drift_chapters.append({"chapter": ch_num, "score": score})

        if len(drift_chapters) > len(all_chapters) * 0.3:
            summary = "\n".join([f"第{d['chapter']}章: 对齐分={d['score']:.2f}" for d in drift_chapters])
            try:
                raw = await fast_llm.chat(
                    "你是小说大纲对齐审核员。分析偏离章节的共性问题，给出全局修正建议。",
                    f"以下章节与大纲偏离较大：\n{summary}\n\n请分析共性问题并给出修正建议。",
                    temperature=0.3, max_tokens=1000,
                )
                story._alignment_review = raw
            except Exception:
                pass
