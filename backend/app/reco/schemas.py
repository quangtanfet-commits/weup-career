"""Pydantic schemas for the recommendations API (spec.md §6, FR-60..63).

The response always surfaces the explainability + human-in-the-loop signals
that ADR-012 mandates: the full ``payload`` (ranked careers + pathway + scores),
the overall ``rationale`` (CP-6), and ``requires_human_confirmation`` (CP-5).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.enums import RecoDecision
from app.reco.models import Recommendation


class ConfirmRequest(BaseModel):
    """Body for ``POST /recommendations/{id}/confirm`` — the human decision."""

    decision: RecoDecision


class RecommendationOut(BaseModel):
    """A recommendation as returned to the client (FR-61)."""

    id: str
    payload: dict[str, Any]
    rationale: str
    requires_human_confirmation: bool
    confirmed_by: str | None
    confirmed_decision: RecoDecision | None
    created_at: datetime

    @classmethod
    def from_model(cls, r: Recommendation) -> RecommendationOut:
        return cls(
            id=r.id,
            payload=r.payload,
            rationale=r.rationale,
            requires_human_confirmation=r.requires_human_confirmation,
            confirmed_by=r.confirmed_by,
            confirmed_decision=r.confirmed_decision,
            created_at=r.created_at,
        )
