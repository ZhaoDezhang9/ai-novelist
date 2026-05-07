"""并行流水线 - 多维度统一质检 + 流水线化写下一章"""
import asyncio
import json
from typing import Optional
from backend.core.models import ChapterRecord, CheckResult, QualityScores
from backend.core.llm_client import fast_llm
from backend.core.utils import extract_json
from backend.generation.prompt_templates import MULTI_DIM_ASSESSMENT_PROMPT


class ParallelPipeline:
    def __init__(self):
        pass

    async def run_multi_dimension_check(
        self,
        story,
        chapter: ChapterRecord,
        hot_memory=None,
    ) -> CheckResult:
        """单次多维度质量评估 — 替代 L1+L2+L3+原创性+对齐+情感 6次调用"""
        chapter_num = chapter.chapter_number

        # 构建评估上下文
        context_parts = []
        wb = story.world_bible
        if wb and wb.rules:
            context_parts.append("【世界观规则】\n" + "\n".join(f"- {r}" for r in wb.rules))

        if story.outline and chapter_num - 1 < len(story.outline):
            outline_node = story.outline[chapter_num - 1]
            context_parts.append(f"【本章大纲】\n目标：{outline_node.get('goal', '')}\n情节点：{', '.join(outline_node.get('plot_points', []))}\n情绪基调：{outline_node.get('emotional_beat', '中性')}\n关键角色：{', '.join(outline_node.get('key_characters', []))}")

        if hot_memory:
            prev_chapters = hot_memory.recent_chapters if hot_memory else []
            if prev_chapters:
                prev_text = "\n".join([
                    f"第{ch.get('number', '?')}章摘要：{ch.get('summary', '')[:200]}"
                    for ch in prev_chapters
                ])
                context_parts.append(f"【前文摘要】\n{prev_text}")

        if story.characters:
            chars = [f"{c.get('name', '')}: {c.get('traits', '')}" for c in story.characters[:5]]
            context_parts.append("【角色设定】\n" + "\n".join(chars))

        context = "\n\n".join(context_parts) if context_parts else "无额外上下文"
        system = MULTI_DIM_ASSESSMENT_PROMPT.format(context=context)
        user = f"请评估以下章节：\n\n{chapter.content[:6000]}"

        try:
            raw = await fast_llm.chat(system, user, temperature=0.2, max_tokens=1500)
            data = json.loads(extract_json(raw))

            quality_scores = QualityScores(
                coherence=float(data.get("coherence", 7)),
                originality=float(data.get("originality", 7)),
                alignment=float(data.get("alignment", 7)),
                emotion=float(data.get("emotion", 7)),
                style=float(data.get("style", 7)),
                overall=float(data.get("overall", 7)),
            )

            min_dim = quality_scores.min_dimension()
            rewrite_needed = data.get("rewrite_needed", False)
            passed = not rewrite_needed and min_dim >= 5 and quality_scores.overall >= 6

            return CheckResult(
                passed=passed,
                layer="multi_dim",
                issues=data.get("issues", []),
                scores={
                    "coherence": quality_scores.coherence,
                    "originality": quality_scores.originality,
                    "alignment": quality_scores.alignment,
                    "emotion": quality_scores.emotion,
                    "style": quality_scores.style,
                    "overall": quality_scores.overall,
                },
                quality_scores=quality_scores,
            )
        except Exception as e:
            return CheckResult(
                passed=False,
                layer="multi_dim",
                issues=[{"type": "check_error", "severity": "critical", "description": f"多维度评估异常: {e}"}],
            )

    async def run_checks_parallel(
        self,
        story,
        chapter: ChapterRecord,
        hot_memory=None,
        only_layers: Optional[set[str]] = None,
    ) -> list[CheckResult]:
        """并行运行质检模块（支持单独重跑失败层）"""
        from backend.quality.consistency import ConsistencyChecker
        from backend.quality.originality import OriginalityChecker
        from backend.quality.alignment import AlignmentChecker
        from backend.quality.emotional_curve import EmotionalCurveAnalyzer

        checker = ConsistencyChecker()
        originality = OriginalityChecker()
        alignment = AlignmentChecker()
        emotion = EmotionalCurveAnalyzer()

        expected_beat = "中性"
        if story.outline and chapter.chapter_number - 1 < len(story.outline):
            expected_beat = story.outline[chapter.chapter_number - 1].get("emotional_beat", "中性")

        check_factories = {
            "L1": lambda: checker.check_l1_self(chapter),
            "L2": lambda: checker.check_l2_cross(story, chapter, hot_memory),
            "L3": lambda: checker.check_l3_world_rules(story, chapter),
            "originality": lambda: originality.check(chapter.content, story.config.genre.value),
            "alignment": lambda: alignment.check(story, chapter),
            "emotion": lambda: emotion.check_against_expected(chapter, expected_beat),
        }

        layers = only_layers if only_layers else set(check_factories.keys())
        tasks_to_run = {k: check_factories[k]() for k in layers if k in check_factories}

        keys = list(tasks_to_run.keys())
        results_raw = await asyncio.gather(*tasks_to_run.values(), return_exceptions=True)

        results = []
        for key, r in zip(keys, results_raw):
            if isinstance(r, Exception):
                results.append(CheckResult(
                    passed=False,
                    layer=key,
                    issues=[{"type": "check_error", "severity": "critical", "description": f"质检模块异常: {str(r)}"}],
                ))
            else:
                results.append(r)  # type: ignore[arg-type]

        return results
