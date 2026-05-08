"""主编排器 - 全流程闭环大脑（Agent + DI + 任务队列）

流水线：创建大纲 → 逐章写 → 多维度质控 → 记忆上下文 → 伏笔管理 → 增量改写 → 入库
优化后每章LLM调用：1次写作 + 1次评估 + 0-3次改写 + 2次后处理 = ≤7次
"""
from typing import AsyncGenerator, Optional

from backend.core.models import (
    Story, StoryConfig, ChapterRecord, ChapterStatus, CheckResult,
)
from backend.core.config import get_settings
from backend.agents.protocols import (
    WorldbuilderAgent, PlotAgent, CharacterAgent,
    ChapterWriterAgent, CriticAgent, StyleAgent,
)
from backend.memory.tiered_memory import TieredMemory
from backend.memory.vector_store import get_vector_store
from backend.management.foreshadowing import ForeshadowingManager
from backend.management.rewrite_engine import RewriteEngine
from backend.core.task_queue import TaskQueue, ChapterTask
from backend.core.container import get_container, Container
from backend.memory import story_db
from backend.generation_status import generation_tracker


class NovelOrchestrator:
    """小说创作总编排器（依赖注入）"""

    def __init__(self, container: Optional[Container] = None):
        c = container or get_container()
        self.settings = get_settings()
        self.worldbuilder: WorldbuilderAgent = c.get(WorldbuilderAgent)
        self.plotter: PlotAgent = c.get(PlotAgent)
        self.char_agent: CharacterAgent = c.get(CharacterAgent)
        self.writer: ChapterWriterAgent = c.get(ChapterWriterAgent)
        self.critic: CriticAgent = c.get(CriticAgent)
        self.style: StyleAgent = c.get(StyleAgent)
        self.memory = TieredMemory()
        self.foreshadowing: ForeshadowingManager = c.get(ForeshadowingManager)
        self.rewrite: RewriteEngine = c.get(RewriteEngine)
        self.task_queue: TaskQueue = c.get(TaskQueue)
        self.task_queue.set_handler(self._handle_chapter_task)

    # ========== 初始化流程 ==========

    async def create_story(self, config: StoryConfig) -> Story:
        import asyncio
        story = Story(config=config)

        # 三个生成任务独立，并行执行以缩短创建时间
        outline_task = asyncio.create_task(self.plotter.generate_plot(story))
        world_task = asyncio.create_task(self.worldbuilder.build_world(story))
        chars_task = asyncio.create_task(self.char_agent.generate_characters(story))

        story.outline = await outline_task
        story.world_bible = await world_task
        story.characters = await chars_task

        await story_db.save_story(story.id, story.model_dump())
        await story_db.save_outline(story.id, story.outline)
        await story_db.save_world_bible(story.id, story.world_bible.model_dump())

        vs = get_vector_store()
        if story.world_bible.rules:
            vs.index_world_rules(story.id, story.world_bible.rules)

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

    # ========== 共享上下文准备 ==========

    async def _prepare_context(self, story: Story, chapter_num: int) -> tuple:
        self.memory.set_story(story)
        await self.memory.restore_caches()
        hot = await self.memory.get_hot(chapter_num)
        warm = self.memory.get_warm()
        cold = self.memory.get_cold()
        semantic_ctx = await self.writer.build_semantic_context(story, chapter_num)
        context = self.writer.build_context(story, hot, warm, cold, semantic_ctx)
        return hot, context

    async def write_next_chapter(self, story: Story) -> ChapterRecord:
        ch_num = story.current_chapter + 1
        hot, context = await self._prepare_context(story, ch_num)

        chapter = await self.writer.write_draft(story, ch_num, context)

        multi_check = await self.critic.review(story, chapter, hot)
        chapter.check_results = [multi_check]

        round_num = 0
        while not multi_check.passed and round_num < self.settings.max_rewrite_rounds:
            round_num += 1
            issues = multi_check.issues
            for i in issues:
                i["layer"] = multi_check.layer
            chapter = await self.rewrite.rewrite_targeted(chapter, issues, context)
            multi_check = await self.critic.review(story, chapter, hot)
            chapter.check_results = [multi_check]
            chapter.rewrites_count = round_num

        chapter.status = ChapterStatus.ACCEPTED
        await story_db.save_chapter(story.id, chapter.chapter_number, chapter.model_dump())

        await self._post_chapter_processing(story, chapter)
        story.current_chapter = chapter.chapter_number
        await story_db.save_story(story.id, story.model_dump())

        return chapter

    async def _post_chapter_processing(self, story: Story, chapter: ChapterRecord):
        """合并后处理：摘要+角色状态(1次) + 伏笔检测(1次)"""
        try:
            await self.memory.update_after_chapter_combined(story, chapter)
        except Exception:
            await self.memory.update_after_chapter(chapter)

        try:
            await self.foreshadowing.update_after_chapter_combined(story, chapter)
        except Exception:
            await self.foreshadowing.update_after_chapter(story, chapter)

    async def write_all_chapters(self, story: Story) -> AsyncGenerator[ChapterRecord, None]:
        """写完全部章节（生成器，逐章返回）"""
        while story.current_chapter < story.config.target_chapters:
            chapter = await self.write_next_chapter(story)
            yield chapter

            if chapter.chapter_number % 10 == 0:
                await self.critic.full_review(story)

    async def write_chapter_stream(self, story: Story) -> AsyncGenerator[dict, None]:
        chapter_num = story.current_chapter + 1
        generation_tracker.start(story.id, chapter_num)
        hot, context = await self._prepare_context(story, chapter_num)

        content_chunks = []
        chapter = None
        auto_save_interval = 50
        token_count = 0

        async for event in self.writer.write_draft_stream(story, chapter_num, context):
            if event.get("type") == "token":
                content_chunks.append(event["data"])
                token_count += 1
                generation_tracker.update(story.id, tokens_received=token_count,
                                          content_preview="".join(content_chunks)[-200:])
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
        multi_check = await self.critic.review(story, chapter, hot)
        chapter.check_results = [multi_check]
        yield {"type": "check_complete", "results": [{"layer": multi_check.layer, "passed": multi_check.passed, "scores": multi_check.scores}]}

        round_num = 0
        while not multi_check.passed and round_num < self.settings.max_rewrite_rounds:
            round_num += 1
            issues = multi_check.issues
            for i in issues:
                i["layer"] = multi_check.layer
            generation_tracker.update(story.id, status="rewriting")
            yield {"type": "rewriting", "round": round_num, "issues_count": len(issues)}
            chapter = await self.rewrite.rewrite_targeted(chapter, issues, context)
            multi_check = await self.critic.review(story, chapter, hot)
            chapter.check_results = [multi_check]
            chapter.rewrites_count = round_num

        generation_tracker.update(story.id, status="saving")
        chapter.status = ChapterStatus.ACCEPTED
        await story_db.save_chapter(story.id, chapter.chapter_number, chapter.model_dump())
        await self._post_chapter_processing(story, chapter)
        story.current_chapter = chapter.chapter_number
        await story_db.save_story(story.id, story.model_dump())

        generation_tracker.finish(story.id)
        yield {"type": "chapter_complete", "chapter_number": chapter.chapter_number, "word_count": chapter.word_count}

    # ========== 任务队列 ==========

    async def submit_all_chapters(self, story: Story) -> list[str]:
        """提交剩余章节到任务队列，返回任务 ID 列表"""
        await self.task_queue.start()
        task_ids = []
        for ch_num in range(story.current_chapter + 1, story.config.target_chapters + 1):
            task = ChapterTask(
                task_id=f"{story.id}_ch{ch_num}",
                story_id=story.id,
                chapter_number=ch_num,
            )
            await self.task_queue.submit(task)
            task_ids.append(task.task_id)
        return task_ids

    async def _handle_chapter_task(self, task: ChapterTask) -> ChapterRecord:
        story = await self.load_story(task.story_id)
        if not story:
            raise ValueError(f"故事 {task.story_id} 不存在")
        story.current_chapter = task.chapter_number - 1
        return await self.write_next_chapter(story)

    # ========== 改写入口 ==========

    async def rewrite_chapter(self, story: Story, chapter_number: int) -> Optional[ChapterRecord]:
        chapter_data = await story_db.load_chapter(story.id, chapter_number)
        if not chapter_data:
            return None

        chapter = ChapterRecord(
            story_id=story.id,
            chapter_number=chapter_number,
            content=chapter_data.get("content", ""),
            word_count=chapter_data.get("word_count", 0),
        )

        hot, context = await self._prepare_context(story, chapter_number)
        multi_check = await self.critic.review(story, chapter, hot)
        issues = multi_check.issues
        for i in issues:
            i["layer"] = multi_check.layer

        if issues:
            chapter = await self.rewrite.rewrite_targeted(chapter, issues, context)
            await story_db.save_chapter(story.id, chapter_number, chapter.model_dump())

        return chapter

    # ========== 助手方法 ==========

    def _all_passed(self, checks: list[CheckResult]) -> bool:
        return all(c.passed for c in checks)

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
            "dimension_min": self.settings.quality_dimension_min,
            "overall_min": self.settings.quality_overall_min,
        }
