"""Conformance trace emitter (Gate B — formal-verify Hard Rule 7).

Env-gated: emits one NDJSON line per modelled state-transition when
`WEUP_TRACE_FILE` is set; a no-op otherwise (zero cost in normal runs / tests).
Traces are replayed against the TLA+ specs in `tla/` to prove the implementation
conforms to the verified model (ConsentLifecycle / AuthTokenLifecycle).

Each line: {"event": "<SpecAction>", "user": "<id>", "state": {...}} — the
`state` mirrors the spec's post-state variables for that user.
"""

from __future__ import annotations

import json
import os
from typing import Any

_ENV = "WEUP_TRACE_FILE"


def emit(event: str, *, user: str, state: dict[str, Any]) -> None:
    """Append one NDJSON trace line if tracing is enabled; else no-op."""
    path = os.environ.get(_ENV)
    if not path:
        return
    line = json.dumps({"event": event, "user": user, "state": state}, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
