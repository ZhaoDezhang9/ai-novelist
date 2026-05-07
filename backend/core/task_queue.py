"""异步任务队列 — asyncio.Queue，支持取消/超时/重试"""
import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, Any
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ChapterTask:
    task_id: str
    story_id: str
    chapter_number: int
    status: TaskStatus = TaskStatus.PENDING
    result: Any = None
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retries: int = 0
    max_retries: int = 3


class TaskQueue:
    def __init__(self, max_workers: int = 1):
        self._queue: asyncio.Queue[ChapterTask] = asyncio.Queue()
        self._tasks: dict[str, ChapterTask] = {}
        self._max_workers = max_workers
        self._workers: list[asyncio.Task] = []
        self._handler: Optional[Callable] = None
        self._running = False

    def set_handler(self, handler: Callable):
        self._handler = handler

    @property
    def pending_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.PENDING)

    @property
    def running_count(self) -> int:
        return sum(1 for t in self._tasks.values() if t.status == TaskStatus.RUNNING)

    async def submit(self, task: ChapterTask):
        self._tasks[task.task_id] = task
        await self._queue.put(task)

    async def start(self):
        if self._running:
            return
        self._running = True
        for _ in range(self._max_workers):
            self._workers.append(asyncio.create_task(self._worker()))

    async def stop(self):
        self._running = False
        for w in self._workers:
            w.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def _worker(self):
        while self._running:
            try:
                task = await asyncio.wait_for(self._queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            if task.status == TaskStatus.CANCELLED:
                continue

            task.status = TaskStatus.RUNNING
            task.started_at = time.time()

            try:
                if self._handler:
                    task.result = await asyncio.wait_for(
                        self._handler(task), timeout=600,
                    )
                task.status = TaskStatus.COMPLETED
            except asyncio.TimeoutError:
                task.error = "任务超时"
                if task.retries < task.max_retries:
                    task.retries += 1
                    task.status = TaskStatus.PENDING
                    await self._queue.put(task)
                else:
                    task.status = TaskStatus.FAILED
            except asyncio.CancelledError:
                task.status = TaskStatus.CANCELLED
            except Exception as e:
                task.error = str(e)
                if task.retries < task.max_retries:
                    task.retries += 1
                    task.status = TaskStatus.PENDING
                    await self._queue.put(task)
                else:
                    task.status = TaskStatus.FAILED

            task.completed_at = time.time()

    def cancel(self, task_id: str):
        task = self._tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED

    def get_status(self, task_id: str) -> Optional[ChapterTask]:
        return self._tasks.get(task_id)

    def list_tasks(self, story_id: Optional[str] = None) -> list[ChapterTask]:
        tasks = list(self._tasks.values())
        if story_id:
            tasks = [t for t in tasks if t.story_id == story_id]
        return tasks
