"""Fixed-window in-memory rate limiting (PT-03, ADR-008).

A dependency-free fixed-window counter, keyed by ``(scope, identity)``. Scopes
map to the ADR-008 buckets (register / [CRED_5F3A6A21] / [CRED_5F3A6A22] + a global ``api`` bucket);
identity is the client IP, or the JWT ``sub`` for the authenticated global
bucket so users behind a shared NAT are limited independently.

The limiter lives on ``app.state.rate_limiter`` so each ``create_app()`` (and
thus each test) gets an isolated counter. In-memory means counts are per
process: with N workers the effective limit is ``limit * N``. That is an
accepted v1 tradeoff for abuse mitigation — see ``docs/security/http-hardening.md``.
"""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable
from math import ceil

from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import Settings
from app.core.exceptions import TokenError
from app.core.security import decode_access_token

# Sweep expired buckets once the table grows past this many keys, so memory
# stays bounded by the active key set within a window rather than growing
# unboundedly across distinct identities.
_PRUNE_THRESHOLD = 10_000


class RateLimiter:
    """Fixed-window counters keyed by ``(scope, identity)``."""

    def __init__(self) -> None:
        # key -> (count, window_start_monotonic)
        self._buckets: dict[tuple[str, str], tuple[int, float]] = {}

    def hit(
        self,
        scope: str,
        identity: str,
        *,
        limit: int,
        window: float,
        now: float,
    ) -> tuple[bool, int]:
        """Register one request. Returns ``(allowed, retry_after_seconds)``.

        ``retry_after_seconds`` is 0 when allowed, else the whole seconds until
        the current window elapses (minimum 1).
        """
        key = (scope, identity)
        entry = self._buckets.get(key)
        if entry is None or now - entry[1] >= window:
            self._maybe_prune(now)
            self._buckets[key] = (1, now)
            return True, 0
        count, start = entry
        count += 1
        if count > limit:
            retry_after = max(1, ceil(window - (now - start)))
            return False, retry_after
        self._buckets[key] = (count, start)
        return True, 0

    def _maybe_prune(self, now: float) -> None:
        if len(self._buckets) < _PRUNE_THRESHOLD:
            return
        # We don't know per-key windows here, so prune anything older than the
        # longest configured window (register, 1h). Conservative but bounded.
        cutoff = now - 3600
        self._buckets = {key: value for key, value in self._buckets.items() if value[1] >= cutoff}


def _classify(request: Request) -> tuple[str | None, str]:
    """Return ``(scope, key_mode)`` for the request, or ``(None, "")`` to skip.

    Only ``/api/v1/*`` is rate-limited; ``/health`` and the doc paths are not.
    """
    path = request.url.path
    if not path.startswith("/api/v1/"):
        return None, ""
    if request.method == "POST":
        if path == "/api/v1/auth/register":
            return "register", "ip"
        if path == "/api/v1/auth/login":
            return "login", "ip"
        if path == "/api/v1/auth/refresh":
            return "refresh", "ip"
    return "api", "sub"


def _identity(request: Request, mode: str, settings: Settings) -> str:
    ip = request.client.host if request.client else "unknown"
    if mode == "sub":
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            try:
                claims = decode_access_token(auth[7:], settings=settings)
                sub = claims.get("sub")
                if sub:
                    return f"sub:{sub}"
            except TokenError:
                pass
    return f"ip:{ip}"


def _rate_limited_response(request: Request, retry_after: int) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    body = {
        "error": {
            "code": "RATE_LIMITED",
            "message": "Quá nhiều yêu cầu, thử lại sau.",
            "details": {"retry_after": retry_after},
            "request_id": request_id,
        }
    }
    return JSONResponse(
        status_code=429,
        content=body,
        headers={"Retry-After": str(retry_after)},
    )


def make_rate_limit_middleware(
    settings: Settings,
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    """Build the rate-limit middleware bound to ``settings``' bucket config."""
    buckets: dict[str, tuple[int, int]] = {
        "register": (
            settings.rate_limit_register_max,
            settings.rate_limit_register_window_seconds,
        ),
        "login": (
            settings.rate_limit_login_max,
            settings.rate_limit_login_window_seconds,
        ),
        "refresh": (
            settings.rate_limit_refresh_max,
            settings.rate_limit_refresh_window_seconds,
        ),
        "api": (
            settings.rate_limit_api_max,
            settings.rate_limit_api_window_seconds,
        ),
    }

    async def rate_limit_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        scope, key_mode = _classify(request)
        if scope is None:
            return await call_next(request)
        limit, window = buckets[scope]
        identity = _identity(request, key_mode, settings)
        limiter: RateLimiter = request.app.state.rate_limiter
        allowed, retry_after = limiter.hit(
            scope, identity, limit=limit, window=window, now=time.monotonic()
        )
        if not allowed:
            return _rate_limited_response(request, retry_after)
        return await call_next(request)

    return rate_limit_middleware
