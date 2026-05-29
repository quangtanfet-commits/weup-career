"""Pydantic schemas for the wellbeing API (FR-71).

The response carries ONLY routing fields — no diagnosis, no risk/severity, no
clinical content (NG-03). ``message`` is the student's own words echoed back.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.core.enums import CounselingTier, SupportRequestStatus
from app.wellbeing.models import SupportRequest


class SupportRequestCreate(BaseModel):
    """A student's request for support. Plain free text, no structured signals."""

    message: str = Field(default="", max_length=4000)


class SupportRequestOut(BaseModel):
    """A referral record (routing only — NO diagnosis/risk fields, NG-03)."""

    id: str
    student_id: str
    counselor_id: str | None
    tier: CounselingTier
    message: str
    status: SupportRequestStatus
    created_at: datetime

    @classmethod
    def from_model(cls, r: SupportRequest) -> SupportRequestOut:
        return cls(
            id=r.id,
            student_id=r.student_id,
            counselor_id=r.counselor_id,
            tier=r.tier,
            message=r.message,
            status=r.status,
            created_at=r.created_at,
        )
