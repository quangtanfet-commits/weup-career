"""Pydantic schemas for the assessment API (spec.md §6, FR-10..15).

Sensitive result content (scores, type code) is returned only on an explicit,
audited read (GET /me/assessments/{id}) — never in the list or submit-ack
responses, which carry metadata only (no payload leak; ADR-011).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import InstrumentType


class InstrumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    type: InstrumentType
    version: str
    is_active: bool


class SubmitRequest(BaseModel):
    """Answers-only submission (NFR-12 / [CRED_0CC1AD1F]: no protected attributes accepted).

    ``answers`` maps an item key (e.g. ``"R_1"``) to a Likert value 1..5.
    """

    answers: dict[str, int] = Field(min_length=1)


class ResultMetaOut(BaseModel):
    """Metadata-only view (no decrypted payload) — safe for submit ack."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    instrument_id: str
    is_sensitive: bool
    version: int
    created_at: datetime


class ResultDetailOut(BaseModel):
    """Full view including the decrypted payload — only via an audited read."""

    id: str
    instrument_id: str
    is_sensitive: bool
    version: int
    created_at: datetime
    payload: dict[str, object]
