"""Structured logging setup for error-fix-engine.

Outputs:
  - Human-readable coloured output to stdout (dev / CI)
  - JSON-lines log file at logs/pipeline.jsonl (for monitoring / ingest)
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

import structlog


def _ensure_log_dir() -> Path:
    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def configure_logging(log_level: str = "INFO") -> None:
    """Call once at process startup to initialise structlog + stdlib logging."""
    log_dir = _ensure_log_dir()
    level = getattr(logging, log_level.upper(), logging.INFO)

    # ── stdlib root logger (receives structlog output) ───────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove any existing handlers so we don't duplicate on re-import
    root_logger.handlers.clear()

    # Console handler – coloured in a real terminal, plain in CI
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    # File handler – JSON lines so they can be grepped / ingested later
    file_handler = logging.FileHandler(log_dir / "pipeline.jsonl", encoding="utf-8")
    file_handler.setLevel(level)
    root_logger.addHandler(file_handler)

    # ── structlog ─────────────────────────────────────────────────────────────
    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    is_tty = os.isatty(sys.stdout.fileno()) if hasattr(sys.stdout, "fileno") else False

    if is_tty:
        # Pretty coloured output for humans
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # JSON for CI / log aggregators
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.BoundLogger:
    """Return a bound structlog logger for *name*."""
    return structlog.get_logger(name)
