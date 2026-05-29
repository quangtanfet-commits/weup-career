"""Pydantic v2 schemas for the account data-rights API (FR-91/92)."""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import AccountStatus, AgeBand, SchoolLevel, UserType

_UPPER = re.compile(r"[A-Z]")
_LOWER = re.compile(r"[a-z]")
_DIGIT = re.compile(r"\d")


class ProfileUpdateRequest(BaseModel):
    """Editable SAFE profile fields only (FR-91).

    Identity / [CRED_22055F75] attributes (``email``, ``age_band``, ``account_status``,
    ``is_deleted``, ``date_of_birth``) are deliberately NOT editable here: they
    drive the consent gate (CP-1) and ownership, so changing them must go through
    dedicated, audited flows — not a generic profile PATCH. Every field is
    optional; only those supplied are updated (partial update).
    """

    model_config = ConfigDict(extra="forbid")

    school_level: SchoolLevel | None = None
    user_type: UserType | None = None


class PasswordChangeRequest(BaseModel):
    """Change password (FR-91): requires the current password to authorise."""

    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=8, max_length=256)

    @field_validator("new_password")
    @classmethod
    def _password_complexity(cls, value: str) -> str:
        # Same complexity rule as registration (FR-06).
        if not (_UPPER.search(value) and _LOWER.search(value) and _DIGIT.search(value)):
            raise ValueError("Mật khẩu phải có chữ hoa, chữ thường và số")
        return value


class ProfileOut(BaseModel):
    """The caller's own profile (FR-91 view), echoing the editable surface."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    date_of_birth: date
    age_band: AgeBand
    user_type: UserType
    school_level: SchoolLevel
    account_status: AccountStatus
    created_at: datetime
    updated_at: datetime


class DeletionOut(BaseModel):
    """Acknowledges a soft-deletion + states when the hard purge becomes due."""

    status: AccountStatus
    deleted_at: datetime
    purge_due_at: datetime
    recovery_window_days: int


class DataExport(BaseModel):
    """The full personal-data export bundle (FR-92, Luật 91/2025 Đ.16).

    Structured JSON. ``assessment_results`` carry DECRYPTED payloads — reading
    them is a sensitive access, so the service writes a CP-3 audit row.
    """

    exported_at: datetime
    subject_id: str
    profile: ProfileOut
    assessment_results: list[dict[str, Any]]
    competency_progress: list[dict[str, Any]]
    domain_phases: list[dict[str, Any]]
    recommendations: list[dict[str, Any]]
