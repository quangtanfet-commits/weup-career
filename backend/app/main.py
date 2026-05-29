"""Application factory: FastAPI app with lifespan, middleware, error handlers."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.database import Database
from app.core.exceptions import AppError, ValidationError
from app.core.logging import configure_logging, get_logger
from app.core.middleware import correlation_id_middleware


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
    return app


def get_app() -> FastAPI:
    """ASGI factory entrypoint (``uvicorn app.main:get_app --factory``).

    Defers settings resolution to call time so importing this module (e.g. in
    tests) does not require production secrets to be present.
    """
    return create_app()
