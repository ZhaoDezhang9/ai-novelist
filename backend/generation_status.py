"""生成状态追踪 — 记录哪些故事正在生成中"""
import asyncio
from typing import Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class GenerationStatus:
    story_id: str
    chapter_number: int
    status: str  # "generating" | "checking" | "rewriting" | "complete" | "idle"
    tokens_received: int = 0
    content_preview: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


class GenerationTracker:
    """全局生成状态追踪器"""

    def __init__(self):
        self._statuses: dict[str, GenerationStatus] = {}

    def start(self, story_id: str, chapter_number: int):
        self._statuses[story_id] = GenerationStatus(
            story_id=story_id,
            chapter_number=chapter_number,
            status="generating",
        )

    def update(self, story_id: str, **kwargs):
        if story_id in self._statuses:
            s = self._statuses[story_id]
            for k, v in kwargs.items():
                if hasattr(s, k):
                    setattr(s, k, v)
            s.updated_at = datetime.now().isoformat()

    def finish(self, story_id: str):
        if story_id in self._statuses:
            self._statuses[story_id].status = "complete"
            self._statuses[story_id].updated_at = datetime.now().isoformat()

    def clear(self, story_id: str):
        self._statuses.pop(story_id, None)

    def get(self, story_id: str) -> Optional[GenerationStatus]:
        return self._statuses.get(story_id)

    def get_all_active(self) -> list[GenerationStatus]:
        return [s for s in self._statuses.values() if s.status != "idle"]


# 全局单例
generation_tracker = GenerationTracker()
