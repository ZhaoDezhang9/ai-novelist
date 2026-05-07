"""结构化日志 - structlog + correlation_id"""
import structlog
import logging
from pathlib import Path
from contextvars import ContextVar
from backend.core.config import get_settings

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def setup_logging():
    settings = get_settings()
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # File handler
    file_handler = logging.FileHandler(settings.log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s"
    ))

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)


def get_logger(**ctx):
    cid = correlation_id_var.get()
    if cid:
        ctx["correlation_id"] = cid
    return structlog.get_logger().bind(**ctx)
