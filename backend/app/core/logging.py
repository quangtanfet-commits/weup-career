"""Structured NDJSON logging (structlog). NEVER logs PII/tokens/sensitive payloads.

Only metadata (event name, actor id, request id, status) is emitted — sensitive
*content* goes to the append-only audit store instead (overview.md §Observability).
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from contextvars import ContextVar
from typing import Any

import structlog

EventDict = MutableMapping[str, Any]

# Correlation id for the current request; bound by middleware.
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)

_PII_KEYS = frozenset(
    {
        "password",
        "hashed_password",
        "token",
        "access_token",
        "refresh_token",
        "token_hash",
        "result_payload",
        "authorization",
        "cookie",
        "set-cookie",
    }
)


def _redact_pii(_logger: Any, _method: str, event_dict: EventDict) -> EventDict:
    """Drop any key that could carry PII / secrets / sensitive payloads."""
    for key in list(event_dict.keys()):
        if key.lower() in _PII_KEYS:
            event_dict[key] = "[REDACTED]"
    return event_dict


def _add_correlation_id(_logger: Any, _method: str, event_dict: EventDict) -> EventDict:
    cid = correlation_id_var.get()
    if cid is not None:
        event_dict["request_id"] = cid
    return event_dict


def configure_logging(level: str = "info") -> None:
    """Configure structlog to emit NDJSON to stdout."""
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(format="%(message)s", level=log_level)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_correlation_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _redact_pii,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "weup-api") -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
