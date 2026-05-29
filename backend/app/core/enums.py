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


class SchoolRole(StrEnum):
    """A user's role *within a school* (FR-80..83), stored on ``SchoolMembership``.

    Orthogonal to ``User.user_type`` (student/working): the same person is a
    ``student`` user_type AND has a ``student`` school role (enrollment), while a
    teacher is a ``student``/``working`` user_type with a ``counselor`` or
    ``school_admin`` school role scoped to one ``school_id``. The school channel
    is DB-relational, not a JWT claim — membership is looked up per request so a
    counselor is only ever authorised within the school they belong to (CP-4).
    """

    STUDENT = "student"
    COUNSELOR = "counselor"
    SCHOOL_ADMIN = "school_admin"


class CounselingTier(StrEnum):
    """Three-tier support model (FR-81, spec §5 CounselingSession.tier 1/2/3).

    Tier 1 = universal content for all students; Tier 2 = targeted group work;
    Tier 3 = individual counselling. Stored as the string "1"/"2"/"3" so the
    column is a small, stable enum that is portable across SQLite/Postgres.
    """

    TIER_1 = "1"
    TIER_2 = "2"
    TIER_3 = "3"


class RiasecCode(StrEnum):
    """Holland RIASEC interest types (FR-32 crosswalk assessment → careers).

    Used to tag ``CareerProfile.riasec_codes`` and to filter ``GET /careers?riasec=``.
    Letters match the RIASEC assessment scoring dimensions (assessments/scoring.py).
    """

    R = "R"  # Realistic
    I = "I"  # Investigative  # noqa: E741 — RIASEC letter, not an ambiguous var
    A = "A"  # Artistic
    S = "S"  # Social
    E = "E"  # Enterprising
    C = "C"  # Conventional


class PathwayType(StrEnum):
    """Phân luồng pathway after a schooling stage (FR-31, Luật GDNN 124/2025).

    ``vocational_secondary`` is the "trường trung học nghề" branch and
    ``gdnn`` the broader giáo dục nghề nghiệp track — both are first-class
    pathways so a career can be reached without academic university study.
    """

    ACADEMIC = "academic"
    VOCATIONAL_SECONDARY = "vocational_secondary"
    GDNN = "gdnn"
    LABOR = "labor"


class TrainingLevel(StrEnum):
    """Trình độ đào tạo a career typically requires (filters GET /careers).

    Coarse rungs spanning the GDNN ↔ academic spectrum so a learner can filter
    careers by how much training they entail (FR-32).
    """

    SECONDARY = "secondary"
    VOCATIONAL = "vocational"
    COLLEGE = "college"
    UNIVERSITY = "university"
    POSTGRADUATE = "postgraduate"


class ContentStatus(StrEnum):
    """Publication state of a versioned ``ContentItem`` (FR-90, NFR-26)."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class RecoDecision(StrEnum):
    """Human decision recorded on a ``Recommendation`` (CP-5, ADR-012).

    A recommendation becomes *effective* only once a person (the owner, a
    guardian, or a counselor) writes one of these via ``POST
    /recommendations/{id}/confirm``. The system NEVER sets it on its own —
    that is the human-in-the-loop invariant (spec.md §8 CP-5).
    """

    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"
