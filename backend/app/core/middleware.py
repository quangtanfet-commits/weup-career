"""Correlation-id middleware (NFR-17): one request id per request.

Reads an inbound ``X-Request-ID`` if present (trusted edge / [CRED_5DA89D27]), else
generates one, binds it for structured logging, and echoes it on the response.
"""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_var

_HEADER = "X-Request-ID"


def _new_request_id() -> str:
    return f"req_{secrets.token_hex(12)}"


async def correlation_id_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    incoming = request.headers.get(_HEADER)
    request_id = incoming or _new_request_id()
    token = correlation_id_var.set(request_id)
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    finally:
        correlation_id_var.reset(token)
    response.headers[_HEADER] = request_id
    return response
