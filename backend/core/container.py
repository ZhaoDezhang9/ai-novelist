"""简易 DI 容器 — 消除硬耦合的组件实例化"""
from typing import Any, Optional


class Container:
    def __init__(self):
        self._services: dict[type, Any] = {}

    def register(self, interface: type, implementation: Any):
        self._services[interface] = implementation

    def get(self, interface: type) -> Any:
        return self._services.get(interface)


def create_container() -> Container:
    from backend.agents.protocols import (
        WorldbuilderAgent, PlotAgent, CharacterAgent,
        ChapterWriterAgent, CriticAgent, StyleAgent,
    )
    from backend.agents.impl import (
        WorldbuilderAgentImpl, PlotAgentImpl, CharacterAgentImpl,
        ChapterWriterAgentImpl, CriticAgentImpl, StyleAgentImpl,
    )
    from backend.management.foreshadowing import ForeshadowingManager
    from backend.management.rewrite_engine import RewriteEngine
    from backend.core.task_queue import TaskQueue

    c = Container()
    c.register(WorldbuilderAgent, WorldbuilderAgentImpl())
    c.register(PlotAgent, PlotAgentImpl())
    c.register(CharacterAgent, CharacterAgentImpl())
    c.register(ChapterWriterAgent, ChapterWriterAgentImpl())
    c.register(CriticAgent, CriticAgentImpl())
    c.register(StyleAgent, StyleAgentImpl())
    c.register(ForeshadowingManager, ForeshadowingManager())
    c.register(RewriteEngine, RewriteEngine())
    c.register(TaskQueue, TaskQueue())
    return c


_container: Optional[Container] = None


def get_container() -> Container:
    global _container
    if _container is None:
        _container = create_container()
    return _container
