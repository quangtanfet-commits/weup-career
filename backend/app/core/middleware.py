"""HTTP middleware: correlation-id (NFR-17) and security headers (PT-05/PT-07).

The correlation-id middleware reads an inbound ``X-Request-ID`` if present
(trusted edge / [CRED_5DA89D27]), else generates one, binds it for structured logging,
and echoes it on the response.

The security-headers middleware stamps a fixed set of hardening headers onto
*every* response (incl. errors). See ``docs/security/http-hardening.md``.
"""

from __future__ import annotations

import secrets
from collections.abc import Awaitable, Callable

from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import correlation_id_var

_HEADER = "X-Request-ID"

# Paths whose responses are exempt from the strict CSP because they serve the
# interactive API docs (Swagger UI / [CRED_5A5DBE3B]), which load CDN scripts/styles that
# ``default-src 'none'`` would block. All other headers still apply to them.
_CSP_EXEMPT_PATHS = frozenset({"/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"})

_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
_HSTS = "max-age=63072000; includeSubDomains"


def make_security_headers_middleware(
    *, is_production: bool
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Build the security-headers middleware bound to the environment.

    HSTS is only emitted in production (dev/test run plain HTTP on localhost, so
    forcing HTTPS there would break local workflows).
    """

    async def security_headers_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["X-Frame-Options"] = "DENY"
        headers["Referrer-Policy"] = "no-referrer"
        headers["Server"] = "WeUp"
        if request.url.path not in _CSP_EXEMPT_PATHS:
            headers["Content-Security-Policy"] = _CSP
        if is_production:
            headers["Strict-Transport-Security"] = _HSTS
        return response

    return security_headers_middleware


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
