"""Conformance trace emitter tests (Gate B, core/trace.py)."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.trace import emit


def test_emit_noop_without_env(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.delenv("WEUP_TRACE_FILE", raising=False)
    # No file is created and no error raised when tracing is disabled.
    emit("ProcessCareerData", user="u-1", state={"consentAtCreation": "active"})


def test_emit_appends_ndjson_when_enabled(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    trace_file = tmp_path / "trace.ndjson"
    monkeypatch.setenv("WEUP_TRACE_FILE", str(trace_file))

    emit("ProcessCareerData", user="u-1", state={"consentAtCreation": "active"})
    emit("GrantConsent", user="u-1", state={"consent": "active"})

    lines = trace_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    # Shape mirrors ConsentLifecycle.ProcessCareerData post-state.
    assert first == {
        "event": "ProcessCareerData",
        "user": "u-1",
        "state": {"consentAtCreation": "active"},
    }
