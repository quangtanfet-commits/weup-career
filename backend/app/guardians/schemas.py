"""Pydantic schemas for the guardian-consent API (FR-03, FR-04)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.core.enums import (
    AssuranceLevel,
    ConsentStatus,
    VerificationMethod,
)


class InviteRequest(BaseModel):
    """A child invites a guardian by email (independent channel)."""

    guardian_email: EmailStr
    relationship: str = Field(min_length=1, max_length=64)

    @field_validator("guardian_email")
    @classmethod
    def _normalize(cls, value: str) -> str:
        return value.strip().lower()


class GuardianLinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    child_user_id: str
    guardian_user_id: str
    relationship: str
    verification_method: VerificationMethod
    assurance_level: AssuranceLevel
    verified_at: datetime | None


class ConsentRequest(BaseModel):
    """A guardian grants consent against a verified link."""

    guardian_link_id: str


class RevokeRequest(BaseModel):
    child_user_id: str


class ConsentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    child_user_id: str
    guardian_link_id: str
    scope: str
    status: ConsentStatus
    granted_at: datetime
    revoked_at: datetime | None
