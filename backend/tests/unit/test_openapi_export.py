"""Unit tests for the OpenAPI export entry point (BE-2).

Covers both sinks (stdout and file) plus ``main()`` so the export module — part
of the frontend drift gate — is fully exercised.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from app import openapi_export


def test_export_to_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    returned = openapi_export.export(None)
    captured = capsys.readouterr().out
    assert captured == returned
    parsed = json.loads(captured)
    assert parsed["openapi"].startswith("3.1")
    assert "ErrorEnvelope" in parsed["components"]["schemas"]


def test_export_to_file(tmp_path: Path) -> None:
    target = tmp_path / "openapi.json"
    returned = openapi_export.export(str(target))
    on_disk = target.read_text(encoding="utf-8")
    assert on_disk == returned
    assert json.loads(on_disk)["openapi"].startswith("3.1")


def test_main_with_path_argument(tmp_path: Path) -> None:
    target = tmp_path / "out.json"
    rc = openapi_export.main([str(target)])
    assert rc == 0
    assert json.loads(target.read_text(encoding="utf-8"))["openapi"].startswith("3.1")


def test_main_no_argument_writes_stdout(capsys: pytest.CaptureFixture[str]) -> None:
    rc = openapi_export.main([])
    assert rc == 0
    assert "openapi" in capsys.readouterr().out
