"""Structured logging helpers for local-first product observability."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from datetime import datetime, timezone
import json
import logging
import sys
from typing import Any, Iterator, TextIO
from uuid import uuid4


_BASE_LOGGER_NAME = "three_agents"
_LOG_CONTEXT: ContextVar[dict[str, Any]] = ContextVar("three_agents_log_context", default={})
_CONFIGURED_STREAM: TextIO | None = None


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_fields(fields: dict[str, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in fields.items() if value is not None}


def current_context() -> dict[str, Any]:
    """Return a shallow copy of the current structured log context."""

    return dict(_LOG_CONTEXT.get())


def bind_context(**fields: Any) -> Token[dict[str, Any]]:
    """Bind structured fields to the current logging context."""

    next_context = current_context()
    next_context.update(_normalize_fields(fields))
    return _LOG_CONTEXT.set(next_context)


def reset_context(token: Token[dict[str, Any]]) -> None:
    """Restore the previous logging context using a token."""

    _LOG_CONTEXT.reset(token)


def clear_context() -> None:
    """Clear the active structured logging context."""

    _LOG_CONTEXT.set({})


@contextmanager
def bound_context(**fields: Any) -> Iterator[None]:
    """Temporarily bind fields to the active structured logging context."""

    token = bind_context(**fields)
    try:
        yield
    finally:
        reset_context(token)


def generate_trace_id() -> str:
    """Generate a new local trace identifier."""

    return uuid4().hex


class JsonLogFormatter(logging.Formatter):
    """Render logs as a single JSON object per line."""

    _RESERVED_ATTRS = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _utc_timestamp(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "event": record.getMessage(),
        }
        payload.update(_normalize_fields(current_context()))

        for key, value in record.__dict__.items():
            if key.startswith("_") or key in self._RESERVED_ATTRS:
                continue
            payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_structured_logging(
    *,
    level: int | str = logging.INFO,
    stream: TextIO | None = None,
    force: bool = False,
) -> logging.Logger:
    """Configure the shared product logger for JSON logs on console."""

    global _CONFIGURED_STREAM

    target_stream = stream or sys.__stderr__
    base_logger = logging.getLogger(_BASE_LOGGER_NAME)

    if base_logger.handlers and not force:
        return base_logger

    handler = logging.StreamHandler(target_stream)
    handler.setFormatter(JsonLogFormatter())

    base_logger.handlers.clear()
    base_logger.addHandler(handler)
    base_logger.setLevel(level)
    base_logger.propagate = False

    _CONFIGURED_STREAM = target_stream
    return base_logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced product logger."""

    suffix = "" if not name else f".{name}"
    return logging.getLogger(f"{_BASE_LOGGER_NAME}{suffix}")


def log_event(
    logger: logging.Logger,
    event: str,
    *,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    """Emit a structured lifecycle event."""

    logger.log(level, str(event), extra=_normalize_fields(fields))


__all__ = [
    "JsonLogFormatter",
    "bind_context",
    "bound_context",
    "clear_context",
    "configure_structured_logging",
    "current_context",
    "generate_trace_id",
    "get_logger",
    "log_event",
    "reset_context",
]
