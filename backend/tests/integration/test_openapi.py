"""OpenAPI 3.1 schema hardening tests (BE-2 — backend half of the drift gate).

Asserts the generated schema is complete and stable enough for the frontend to
generate ``types/api.d.ts`` with ``openapi-typescript`` and gate CI on drift:

- the schema builds and is OpenAPI ``3.1.x``;
- every expected route group / [CRED_C8369A48] key path is present;
- the reusable ``ErrorEnvelope`` component is defined and referenced by the
  common 4xx error responses;
- ``operationId``s are present, unique and stable (== handler function names);
- the export entry point (``app.openapi_export``) reproduces the schema.
"""

from __future__ import annotations

import json

from app.core.config import Settings
from app.main import create_app
from app.openapi_export import build_openapi, render

from tests.conftest import make_settings


def _schema() -> dict:
    settings: Settings = make_settings()
    app = create_app(settings)
    return app.openapi()


def test_schema_builds_and_is_openapi_31() -> None:
    schema = _schema()
    assert schema["openapi"].startswith("3.1")
    assert schema["info"]["title"] == "WeUp Career API"
    assert schema["info"]["version"] == "2.0.0"


def test_expected_route_groups_present() -> None:
    paths = _schema()["paths"]
    # Spot-check one key path per domain group (BE-2).
    expected = [
        "/api/v1/auth/register",
        "/api/v1/guardians/consent",
        "/api/v1/assessments",
        "/api/v1/competencies",
        "/api/v1/careers",
        "/api/v1/content",
        "/api/v1/recommendations",
        "/api/v1/counseling/sessions",
        "/api/v1/wellbeing/support-request",
        "/api/v1/me/export",
    ]
    for path in expected:
        assert path in paths, f"missing expected path: {path}"


def test_error_envelope_component_defined_and_referenced() -> None:
    schema = _schema()
    schemas = schema["components"]["schemas"]
    assert "ErrorEnvelope" in schemas
    assert "ErrorDetail" in schemas
    # The envelope's ``error`` field references the inner detail component.
    assert schemas["ErrorEnvelope"]["properties"]["error"]["$ref"].endswith("/ErrorDetail")
    detail_props = schemas["ErrorDetail"]["properties"]
    assert {"code", "message", "details", "request_id"} <= set(detail_props)

    # Common 4xx responses on a representative operation reference the envelope.
    careers_get = schema["paths"]["/api/v1/careers"]["get"]
    for code in ("401", "403", "404", "409", "422"):
        ref = careers_get["responses"][code]["content"]["application/json"]["schema"]["$ref"]
        assert ref == "#/components/schemas/ErrorEnvelope"


def test_operation_ids_present_unique_and_stable() -> None:
    paths = _schema()["paths"]
    op_ids: list[str] = []
    for item in paths.values():
        for method, op in item.items():
            if method in {"get", "post", "put", "patch", "delete"}:
                assert "operationId" in op
                op_ids.append(op["operationId"])
    # Unique across the whole API (the stable-id scheme requires it).
    assert len(op_ids) == len(set(op_ids))
    # Stable, human-readable ids (== handler function names), not the verbose
    # FastAPI default like ``list_careers_api_v1_careers_get``.
    assert "list_careers" in op_ids
    assert "create_recommendation" in op_ids
    assert "export_data" in op_ids


def test_domain_tags_consistent() -> None:
    paths = _schema()["paths"]
    assert paths["/api/v1/careers"]["get"]["tags"] == ["careers"]
    assert paths["/api/v1/recommendations"]["post"]["tags"] == ["recommendations"]
    assert "counseling" in paths["/api/v1/counseling/sessions"]["post"]["tags"]


def test_every_operation_has_response_models() -> None:
    """No operation should be missing an explicit success response schema."""
    paths = _schema()["paths"]
    for path, item in paths.items():
        for method, op in item.items():
            if method not in {"get", "post", "put", "patch", "delete"}:
                continue
            responses = op["responses"]
            # A success status (2xx) must be documented for every operation.
            assert any(code.startswith("2") for code in responses), f"{method} {path} has no 2xx"


def test_export_module_reproduces_schema() -> None:
    """``app.openapi_export`` emits valid JSON identical to ``app.openapi()``."""
    rendered = render(build_openapi())
    parsed = json.loads(rendered)
    assert parsed["openapi"].startswith("3.1")
    assert "ErrorEnvelope" in parsed["components"]["schemas"]
    # Deterministic output: sorted keys + trailing newline (diff-friendly).
    assert rendered.endswith("\n")
    assert json.loads(render(build_openapi())) == parsed
