"""主编排器 - 全流程闭环大脑

流水线：创建大纲 → 逐章写 → 三层防御质控 → 记忆上下文 → 伏笔管理 → 增量改写 → 入库
"""
import asyncio
from typing import AsyncGenerator, Optional

from backend.core.models import (
    Story, StoryConfig, ChapterRecord, ChapterStatus,
    CheckResult, HotMemory, WarmMemory, ColdMemory, ForeshadowingItem,
)
from backend.core.llm_client import main_llm, fast_llm
from backend.core.config import get_settings
from backend.memory import story_db
from backend.memory.tiered_memory import TieredMemory
from backend.memory.context_builder import ContextBuilder
from backend.generation.outline_engine import OutlineEngine
from backend.generation.chapter_writer import ChapterWriter
from backend.pipeline.parallel_pipe import ParallelPipeline
from backend.quality.consistency import ConsistencyChecker
from backend.quality.originality import OriginalityChecker
from backend.quality.alignment import AlignmentChecker
from backend.quality.emotional_curve import EmotionalCurveAnalyzer
from backend.management.foreshadowing import ForeshadowingManager
from backend.management.style_quant import StyleQuantifier
from backend.management.rewrite_engine import RewriteEngine
from backend.generation_status import generation_tracker


class NovelOrchestrator:
    """小说创作总编排器"""

    def __init__(self):
        self.settings = get_settings()
        self.memory = TieredMemory()
        self.context_builder = ContextBuilder()
        self.outline_engine = OutlineEngine()
        self.chapter_writer = ChapterWriter()
        self.pipeline = ParallelPipeline()
        self.consistency = ConsistencyChecker()
        self.originality = OriginalityChecker()
        self.alignment = AlignmentChecker()
        self.emotion = EmotionalCurveAnalyzer()
        self.foreshadowing = ForeshadowingManager()
        self.style_quant = StyleQuantifier()
        self.rewrite = RewriteEngine()

    # ========== 初始化流程 ==========

    async def create_story(self, config: StoryConfig) -> Story:
        """创建新故事：生成大纲、世界观、角色设定"""
        story = Story(config=config)

        story.outline = await self.outline_engine.generate(story)
        story.world_bible = await self.outline_engine.generate_world_bible(story)
        story.characters = await self.outline_engine.generate_characters(story)

        await story_db.save_story(story.id, story.model_dump())
        await story_db.save_outline(story.id, story.outline)
        await story_db.save_world_bible(story.id, story.world_bible.model_dump())

        return story

    async def load_story(self, story_id: str) -> Optional[Story]:
        """加载已有故事"""
        data = await story_db.load_story(story_id)
        if not data:
            return None
        story = Story(**data)
        story.outline = await story_db.load_outline(story_id) or []
        wb = await story_db.load_world_bible(story_id)
        if wb:
            from backend.core.models import WorldBible
            story.world_bible = WorldBible(**wb)
        return story

    # ========== 逐章写作主循环 ==========

    async def write_next_chapter(self, story: Story) -> ChapterRecord:
        """写下一章：完整流水线"""
        self.memory.set_story(story)

        context = self.context_builder.build_master_prompt(
            story=story,
            hot_memory=await self.memory.get_hot(story.current_chapter + 1),
            warm_memory=self.memory.get_warm(),
            cold_memory=self.memory.get_cold(),
        )

        chapter = await self.chapter_writer.write_draft(
            story=story,
            chapter_number=story.current_chapter + 1,
            context=context,
        )

        checks = await self.pipeline.run_checks_parallel(
            story=story,
            chapter=chapter,
            hot_memory=await self.memory.get_hot(story.current_chapter + 1),
        )
        chapter.check_results = checks

        round_num = 0
        while not self._all_passed(checks) and round_num < self.settings.max_rewrite_rounds:
            round_num += 1
            issues = self._collect_issues(checks)
            chapter = await self.rewrite.rewrite_targeted(chapter, issues, context)

            # 只重跑失败的检查项，提高效率
            failed_layers = {c.layer for c in checks if not c.passed}
            new_checks = await self.pipeline.run_checks_parallel(
                story=story, chapter=chapter,
                hot_memory=await self.memory.get_hot(story.current_chapter + 1),
                only_layers=failed_layers,
            )
            # 合并结果：用新检查结果替换对应层的旧结果
            new_by_layer = {c.layer: c for c in new_checks}
            checks = [new_by_layer.get(c.layer, c) for c in checks]
            chapter.check_results = checks
            chapter.rewrites_count = round_num

        chapter.status = ChapterStatus.ACCEPTED
        await story_db.save_chapter(story.id, chapter.chapter_number, chapter.model_dump())

        await self.memory.update_after_chapter(chapter)
        story.current_chapter = chapter.chapter_number

        await self.foreshadowing.update_after_chapter(story, chapter)
        await story_db.save_story(story.id, story.model_dump())

        return chapter

    async def write_all_chapters(self, story: Story) -> AsyncGenerator[ChapterRecord, None]:
        """写完全部章节（生成器，逐章返回）"""
        while story.current_chapter < story.config.target_chapters:
            chapter = await self.write_next_chapter(story)
            yield chapter

            if chapter.chapter_number % 10 == 0:
                await self.alignment.full_review(story)

    async def write_chapter_stream(self, story: Story) -> AsyncGenerator[dict, None]:
        """流式写章节 - 供 SSE 推送，自动保存草稿"""
        self.memory.set_story(story)
        chapter_num = story.current_chapter + 1
        generation_tracker.start(story.id, chapter_num)

        context = self.context_builder.build_master_prompt(
            story=story,
            hot_memory=await self.memory.get_hot(chapter_num),
            warm_memory=self.memory.get_warm(),
            cold_memory=self.memory.get_cold(),
        )

        content_chunks = []
        chapter = None
        auto_save_interval = 50  # 每50个token自动保存一次
        token_count = 0

        async for event in self.chapter_writer.write_draft_stream(story, chapter_num, context):
            if event.get("type") == "token":
                content_chunks.append(event["data"])
                token_count += 1
                generation_tracker.update(story.id, tokens_received=token_count,
                                          content_preview="".join(content_chunks)[-200:])
                # 自动保存草稿
                if token_count % auto_save_interval == 0:
                    draft_content = "".join(content_chunks)
                    await story_db.save_chapter(story.id, chapter_num, {
                        "id": f"{story.id}_ch{chapter_num}",
                        "story_id": story.id,
                        "chapter_number": chapter_num,
                        "content": draft_content,
                        "word_count": len(draft_content),
                        "status": "draft",
                    })
                yield event
            elif event.get("type") == "complete":
                chapter = ChapterRecord(**event["chapter"])
                break

        if not chapter:
            generation_tracker.finish(story.id)
            yield {"type": "error", "message": "草稿生成失败"}
            return

        generation_tracker.update(story.id, status="checking")
        checks = await self.pipeline.run_checks_parallel(
            story=story, chapter=chapter,
            hot_memory=await self.memory.get_hot(chapter_num),
        )
        chapter.check_results = checks
        yield {"type": "check_complete", "results": [{"layer": c.layer, "passed": c.passed} for c in checks]}

        round_num = 0
        while not self._all_passed(checks) and round_num < self.settings.max_rewrite_rounds:
            round_num += 1
            issues = self._collect_issues(checks)
            generation_tracker.update(story.id, status="rewriting")
            yield {"type": "rewriting", "round": round_num, "issues_count": len(issues)}
            chapter = await self.rewrite.rewrite_targeted(chapter, issues, context)

            # 只重跑失败的检查项
            failed_layers = {c.layer for c in checks if not c.passed}
            new_checks = await self.pipeline.run_checks_parallel(
                story=story, chapter=chapter,
                hot_memory=await self.memory.get_hot(chapter_num),
                only_layers=failed_layers,
            )
            # 合并结果：用新检查结果替换对应层的旧结果
            new_by_layer = {c.layer: c for c in new_checks}
            checks = [new_by_layer.get(c.layer, c) for c in checks]
            chapter.check_results = checks
            chapter.rewrites_count = round_num

        generation_tracker.update(story.id, status="saving")
        chapter.status = ChapterStatus.ACCEPTED
        await story_db.save_chapter(story.id, chapter.chapter_number, chapter.model_dump())
        await self.memory.update_after_chapter(chapter)
        story.current_chapter = chapter.chapter_number
        await self.foreshadowing.update_after_chapter(story, chapter)
        await story_db.save_story(story.id, story.model_dump())

        generation_tracker.finish(story.id)
        yield {"type": "chapter_complete", "chapter_number": chapter.chapter_number, "word_count": chapter.word_count}

    # ========== 助手方法 ==========

    def _all_passed(self, checks: list[CheckResult]) -> bool:
        return all(c.passed for c in checks if c.layer in ("L1", "L2", "L3"))

    def _collect_issues(self, checks: list[CheckResult]) -> list[dict]:
        issues = []
        for c in checks:
            for issue in c.issues:
                issue["layer"] = c.layer
                issues.append(issue)
        return issues

    # ========== 质量门禁参数 ==========

    @property
    def quality_thresholds(self) -> dict:
        return {
            "ngram_overlap": self.settings.ngram_overlap_threshold,
            "template_similarity": self.settings.template_similarity_threshold,
            "vocab_diversity": self.settings.vocab_diversity_threshold,
            "twist_density": self.settings.twist_density_min,
            "alignment_score": self.settings.alignment_score_min,
        }
