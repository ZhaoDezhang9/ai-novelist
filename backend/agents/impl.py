"""Agent 实现 — 委托给现有模块"""
from typing import AsyncGenerator, Optional
from backend.agents.protocols import (
    WorldbuilderAgent, PlotAgent, CharacterAgent,
    ChapterWriterAgent, CriticAgent, StyleAgent,
)
from backend.core.models import Story, WorldBible, ChapterRecord, CheckResult, StyleVector
from backend.generation.outline_engine import OutlineEngine
from backend.generation.chapter_writer import ChapterWriter
from backend.memory.context_builder import ContextBuilder
from backend.management.style_quant import StyleQuantifier


class WorldbuilderAgentImpl(WorldbuilderAgent):
    def __init__(self):
        self._engine = OutlineEngine()

    async def build_world(self, story: Story) -> WorldBible:
        return await self._engine.generate_world_bible(story)


class PlotAgentImpl(PlotAgent):
    def __init__(self):
        self._engine = OutlineEngine()

    async def generate_plot(self, story: Story) -> list[dict]:
        return await self._engine.generate(story)


class CharacterAgentImpl(CharacterAgent):
    def __init__(self):
        self._engine = OutlineEngine()

    async def generate_characters(self, story: Story) -> list[dict]:
        return await self._engine.generate_characters(story)


class ChapterWriterAgentImpl(ChapterWriterAgent):
    def __init__(self):
        self._writer = ChapterWriter()
        self._context = ContextBuilder()

    async def write_draft(self, story: Story, chapter_number: int, context: str,
                          temperature: Optional[float] = None) -> ChapterRecord:
        return await self._writer.write_draft(story, chapter_number, context, temperature)

    async def write_draft_stream(self, story: Story, chapter_number: int, context: str,
                                 temperature: Optional[float] = None) -> AsyncGenerator[dict, None]:
        async for event in self._writer.write_draft_stream(story, chapter_number, context, temperature):
            yield event

    def build_context(self, story: Story, hot, warm, cold,
                      semantic_context: dict | None = None) -> str:
        return self._context.build_master_prompt(story, hot, warm, cold, semantic_context)

    async def build_semantic_context(self, story: Story, chapter_number: int) -> dict | None:
        return await self._context.build_semantic_context(story, chapter_number)


class CriticAgentImpl(CriticAgent):
    async def review(self, story: Story, chapter: ChapterRecord, hot_memory=None) -> CheckResult:
        from backend.pipeline.parallel_pipe import ParallelPipeline
        pipeline = ParallelPipeline()
        return await pipeline.run_multi_dimension_check(story, chapter, hot_memory)

    async def review_parallel(self, story: Story, chapter: ChapterRecord, hot_memory=None,
                              only_layers: Optional[set[str]] = None) -> list[CheckResult]:
        from backend.pipeline.parallel_pipe import ParallelPipeline
        pipeline = ParallelPipeline()
        return await pipeline.run_checks_parallel(story, chapter, hot_memory, only_layers)

    async def full_review(self, story: Story):
        from backend.quality.alignment import AlignmentChecker
        alignment = AlignmentChecker()
        await alignment.full_review(story)


class StyleAgentImpl(StyleAgent):
    def __init__(self):
        self._quant = StyleQuantifier()

    def get_preset(self, style_name: str) -> StyleVector:
        return self._quant.get_preset(style_name)

    def from_text(self, text: str) -> StyleVector:
        return self._quant.from_text(text)

    def compare(self, target: StyleVector, actual: StyleVector) -> float:
        return self._quant.compare(target, actual)
