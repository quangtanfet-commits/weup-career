"""Application factory: FastAPI app with lifespan, middleware, error handlers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.exceptions import AppError, ValidationError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import correlation_id_middleware
from app.core.schemas import ErrorEnvelope

# Common error responses advertised on (almost) every operation so the generated
# OpenAPI 3.1 schema documents the structured error envelope. Mapped per HTTP
# status to the reusable ``ErrorEnvelope`` component (BE-2 — drift gate).
_ERROR_ENVELOPE_REF = {"$ref": "#/components/schemas/ErrorEnvelope"}
_COMMON_ERROR_STATUSES: dict[str, str] = {
    "401": "Authentication required or token invalid",
    "403": "Permission denied / consent required",
    "404": "Resource not found",
    "409": "Conflict",
    "422": "Validation error",
}


def _unique_operation_id(route: APIRoute) -> str:
    """Stable ``operationId`` = the route handler's function name.

    Handler names are unique across all routers (verified in CI by the OpenAPI
    test), so this yields clean, stable ids (e.g. ``list_careers``) that do not
    churn when a path or tag changes — keeping the frontend's generated
    ``types/api.d.ts`` diff minimal (BE-2).
    """
    return route.name


def _error_body(
    code: str, message: str, request: Request, details: dict[str, Any]
) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": getattr(request.state, "request_id", None),
        }
    }


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    logger = get_logger()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        app.state.settings = settings
        app.state.db = Database(settings)
        logger.info("app.startup", environment=settings.environment)
        try:
            yield
        finally:
            await app.state.db.dispose()
            logger.info("app.shutdown")

    app = FastAPI(
        title="WeUp Career API",
        version="2.0.0",
        lifespan=lifespan,
        openapi_url="/api/v1/openapi.json",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        generate_unique_id_function=_unique_operation_id,
    )

    app.state.settings = settings
    app.add_middleware(BaseHTTPMiddleware, dispatch=correlation_id_middleware)
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.exception_handler(AppError)
    async def _app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        if exc.status_code >= 500:
            logger.error("app.error", code=exc.code, status=exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_body(exc.code, exc.message, request, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        err = ValidationError()
        safe_errors = [
            {
                "loc": list(e.get("loc", [])),
                "msg": str(e.get("msg", "")),
                "type": str(e.get("type", "")),
            }
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=err.status_code,
            content=_error_body(err.code, err.message, request, {"errors": safe_errors}),
        )

    @app.exception_handler(Exception)
    async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error("app.unhandled", error=type(exc).__name__)
        return JSONResponse(
            status_code=500,
            content=_error_body("INTERNAL_ERROR", "Lỗi nội bộ", request, {}),
        )

    app.include_router(api_router)

    def custom_openapi() -> dict[str, Any]:
        """Build the OpenAPI 3.1 schema once and harden it (BE-2).

        - Registers the reusable ``ErrorEnvelope`` component.
        - Advertises the structured error envelope on the common 4xx responses
          (401/403/404/409/422) for every operation that does not already
          declare them, so the generated TypeScript client types the error
          contract instead of falling back to ``unknown``.

        Cached on ``app.openapi_schema`` (FastAPI's standard memoization) so the
        cost is paid once per process.
        """
        if app.openapi_schema:
            return app.openapi_schema

        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
        )

        components = schema.setdefault("components", {})
        schemas = components.setdefault("schemas", {})
        # Pydantic v2 returns the top-level model schema with nested models under
        # ``$defs``; flatten so ErrorEnvelope + ErrorDetail are first-class
        # components referenceable as #/components/schemas/<name>.
        envelope = ErrorEnvelope.model_json_schema(ref_template="#/components/schemas/{model}")
        for name, definition in envelope.pop("$defs", {}).items():
            schemas.setdefault(name, definition)
        schemas.setdefault("ErrorEnvelope", envelope)

        for path_item in schema.get("paths", {}).values():
            for method, operation in path_item.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                responses = operation.setdefault("responses", {})
                for code, description in _COMMON_ERROR_STATUSES.items():
                    # Overwrite (not setdefault): FastAPI auto-injects a 422 typed
                    # as ``HTTPValidationError``, but our exception handlers return
                    # the structured ErrorEnvelope for *every* 4xx (incl. 422), so
                    # the schema must advertise the envelope to match runtime.
                    responses[code] = {
                        "description": description,
                        "content": {"application/json": {"schema": _ERROR_ENVELOPE_REF}},
                    }

        app.openapi_schema = schema
        return schema

    app.openapi = custom_openapi  # type: ignore[method-assign]
    return app


def get_app() -> FastAPI:
    """ASGI factory entrypoint (``uvicorn app.main:get_app --factory``).

    Defers settings resolution to call time so importing this module (e.g. in
    tests) does not require production secrets to be present.
    """
    return create_app()
