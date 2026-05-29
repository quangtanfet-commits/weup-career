"""Shared domain enums (spec.md §5)."""

from __future__ import annotations

from enum import StrEnum


class AgeBand(StrEnum):
    UNDER_16 = "under_16"
    BAND_16_17 = "16_17"
    ADULT = "adult"


class UserType(StrEnum):
    STUDENT = "student"
    WORKING = "working"


class SchoolLevel(StrEnum):
    PRIMARY = "primary"
    LOWER_SECONDARY = "lower_secondary"
    UPPER_SECONDARY = "upper_secondary"
    TERTIARY = "tertiary"
    NONE = "none"


class AccountStatus(StrEnum):
    ACTIVE = "active"
    PENDING_GUARDIAN_CONSENT = "pending_guardian_consent"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class VerificationMethod(StrEnum):
    EMAIL = "email"
    VNEID = "vneid"
    MANUAL = "manual"


class AssuranceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class InstrumentType(StrEnum):
    RIASEC = "riasec"
    VIPS = "vips"
    MBTI = "mbti"


class ConsentStatus(StrEnum):
    ACTIVE = "active"
    REVOKED = "revoked"


class Role(StrEnum):
    STUDENT = "student"
    WORKING = "working"
    GUARDIAN = "guardian"
    COUNSELOR = "counselor"
    SCHOOL_ADMIN = "school_admin"
    CONTENT_EDITOR = "content_editor"
