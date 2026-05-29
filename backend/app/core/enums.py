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


class CompetencyArea(StrEnum):
    """Three ABCD learning areas (ADR-013). 12 competencies split across them."""

    A_PERSONAL = "A_personal"
    B_EXPLORATION = "B_exploration"
    C_BUILDING = "C_building"


class Depth(StrEnum):
    """NCDG K-A-R cognitive-depth axis (ADR-013, CTGDPT 2018).

    Ordering K < A < R is load-bearing for CP-8 (depth only advances). The
    numeric rank lives in ``DEPTH_RANK``; "none" (rank 0) is not a member here —
    absence of progress is represented by having no ``LearnerProgress`` row.
    """

    K = "K"
    A = "A"
    R = "R"


# Depth -> numeric rank (spec.md §8 CP-8 mapping: 0=none, 1=K, 2=A, 3=R).
DEPTH_RANK: dict[Depth, int] = {Depth.K: 1, Depth.A: 2, Depth.R: 3}

# Vietnamese display labels for the depth axis (CTGDPT 2018, spec FR-21 / [CRED_E6E0CFB4] §item 5).
DEPTH_LABEL_VI: dict[Depth, str] = {
    Depth.K: "Nhận biết",
    Depth.A: "Thực hiện-Vận dụng",
    Depth.R: "Phản tư",
}


def depth_rank(depth: Depth) -> int:
    """Numeric rank of a depth (K=1, A=2, R=3) for monotonic comparison (CP-8)."""
    return DEPTH_RANK[depth]


class DevPhase(StrEnum):
    """ECG career-development-stage axis (ADR-013), orthogonal to Depth.

    Students: inferred from ``school_level`` (with allowed deviation). Working
    users: may hold several phases at once across domains (non-linear ABCD).
    """

    AWARENESS = "awareness"
    EXPLORATION = "exploration"
    PLANNING = "planning"


class Role(StrEnum):
    STUDENT = "student"
    WORKING = "working"
    GUARDIAN = "guardian"
    COUNSELOR = "counselor"
    SCHOOL_ADMIN = "school_admin"
    CONTENT_EDITOR = "content_editor"
