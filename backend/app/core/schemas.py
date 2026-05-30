"""Cross-cutting API schemas.

The :class:`ErrorEnvelope` mirrors the runtime error body produced by the
exception handlers in :mod:`app.main`
(``{"error": {"code", "message", "details", "request_id"}}``). It exists so the
OpenAPI 3.1 schema can *advertise* the error contract as a reusable component
(``#/components/schemas/ErrorEnvelope``), which the frontend's
``openapi-typescript`` drift gate consumes. It is metadata only — the handlers
keep emitting the same dict; this just gives that dict a name in the schema.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """The inner error object of the structured error envelope."""

    code: str = Field(description="Stable machine-readable error code (e.g. NOT_FOUND).")
    message: str = Field(description="Human-readable message (Vietnamese).")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured context (e.g. validation errors).",
    )
    request_id: str | None = Field(
        default=None, description="Correlation id for this request, if assigned."
    )


class ErrorEnvelope(BaseModel):
    """Top-level error response body returned for every 4xx/5xx error."""

    error: ErrorDetail
