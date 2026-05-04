"""并行流水线 - 并行的章节质检 + 流水线化写下一章"""
import asyncio
from typing import Optional
from backend.core.models import Story, ChapterRecord, CheckResult


class ParallelPipeline:
    def __init__(self):
        pass

    async def run_checks_parallel(
        self,
        story,
        chapter: ChapterRecord,
        hot_memory=None,
        only_layers: Optional[set[str]] = None,
    ) -> list[CheckResult]:
        """并行运行质检模块
        
        Args:
            only_layers: 如果指定，只运行这些层的检查（用于改写后只重跑失败项）
        """
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

        # 定义所有检查任务
        all_checks = {
            "L1": checker.check_l1_self(chapter),
            "L2": checker.check_l2_cross(story, chapter, hot_memory),
            "L3": checker.check_l3_world_rules(story, chapter),
            "originality": originality.check(chapter.content, story.config.genre.value),
            "alignment": alignment.check(story, chapter),
            "emotion": emotion.check_against_expected(chapter, expected_beat),
        }

        # 如果指定了 only_layers，只运行那些检查
        if only_layers:
            tasks_to_run = {k: v for k, v in all_checks.items() if k in only_layers}
        else:
            tasks_to_run = all_checks

        # 并行执行
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
                results.append(r)

        return results

    async def parallel_write_and_checks(
        self,
        draft_coro,
        story,
        chapter_number: int,
        hot_memory=None,
    ):
        """写草稿的同时预加载质检上下文（优化）"""
        from backend.quality.consistency import ConsistencyChecker
        from backend.quality.originality import OriginalityChecker
        from backend.quality.alignment import AlignmentChecker

        # 并行：写草稿 + 预加载质检器
        checker = ConsistencyChecker()
        originality = OriginalityChecker()
        alignment = AlignmentChecker()

        chapter = await draft_coro

        checks = await self.run_checks_parallel(story, chapter, hot_memory)
        return chapter, checks
