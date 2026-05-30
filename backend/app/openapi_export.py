"""Export the app's OpenAPI 3.1 schema (BE-2 — frontend drift gate).

The frontend generates ``types/api.d.ts`` from this schema with
``openapi-typescript`` and gates CI on drift. This module writes the exact
``app.openapi()`` output (the hardened schema from :func:`app.main.create_app`,
incl. the ``ErrorEnvelope`` component and stable ``operationId``s) as JSON.

Usage::

    python -m app.openapi_export              # → stdout
    python -m app.openapi_export openapi.json # → file

Importing the app does not require production secrets (settings are resolved
lazily via the factory), and building the schema runs no I/O, so this is safe to
call in CI without a database.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.main import create_app


def build_openapi() -> dict[str, Any]:
    """Return the application's hardened OpenAPI 3.1 schema as a dict."""
    app = create_app()
    return app.openapi()


def render(schema: dict[str, Any]) -> str:
    """Serialize the schema to deterministic, diff-friendly JSON."""
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def export(path: str | None = None) -> str:
    """Write the schema to ``path`` (or stdout when ``None``); return the JSON."""
    payload = render(build_openapi())
    if path is None:
        sys.stdout.write(payload)
    else:
        Path(path).write_text(payload, encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    export(args[0] if args else None)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())
