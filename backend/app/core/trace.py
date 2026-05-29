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

# Abstraction map: concrete refresh-token hash -> symbolic spec id (t1, t2, ...).
# Populated only while tracing is enabled (no growth in normal runs).
_token_labels: dict[str, str] = {}


def emit(event: str, *, user: str, state: dict[str, Any]) -> None:
    """Append one NDJSON trace line if tracing is enabled; else no-op."""
    path = os.environ.get(_ENV)
    if not path:
        return
    line = json.dumps({"event": event, "user": user, "state": state}, separators=(",", ":"))
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def token_label(token_hash: str) -> str:
    """Stable symbolic id for a refresh-token hash (Gate B AuthTokenLifecycle).

    No-op (returns "") unless tracing is enabled, so production never accrues
    the map. Within a traced uvicorn process the map persists across requests,
    giving a consistent t1/t2/... abstraction for the spec replay.
    """
    if not os.environ.get(_ENV):
        return ""
    label = _token_labels.get(token_hash)
    if label is None:
        label = f"t{len(_token_labels) + 1}"
        _token_labels[token_hash] = label
    return label
