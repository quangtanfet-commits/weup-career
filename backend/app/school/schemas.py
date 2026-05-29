"""Pydantic schemas for the school-channel API (spec.md §6, FR-80..83).

The student-view schemas deliberately carry only de-sensitized signals: a
roster identity, competency depth/dev_phase, and a short derived assessment
code — never the raw encrypted RIASEC/VIPS/MBTI payload or free text (FR-83,
NFR-10).
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.core.enums import CompetencyArea, CounselingTier, Depth, DevPhase, SchoolRole
from app.school.models import SchoolClass
from app.school.service import (
    DesensitizedAssessment,
    RosterEntry,
    StudentProgressView,
)


class RosterEntryOut(BaseModel):
    user_id: str
    email: str
    class_id: str | None

    @classmethod
    def from_entry(cls, e: RosterEntry) -> RosterEntryOut:
        return cls(user_id=e.user_id, email=e.email, class_id=e.class_id)


class CreateClassRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    grade: str = Field(default="", max_length=16)


class SchoolClassOut(BaseModel):
    id: str
    school_id: str
    name: str
    grade: str

    @classmethod
    def from_model(cls, k: SchoolClass) -> SchoolClassOut:
        return cls(id=k.id, school_id=k.school_id, name=k.name, grade=k.grade)


class AssignMemberRequest(BaseModel):
    """Enroll/assign a user as student or counselor in a school (FR-80).

    ``role`` is constrained to the assignable school roles; the service rejects
    anything else. ``class_id`` is optional class scoping.
    """

    user_id: str = Field(min_length=1)
    role: SchoolRole
    class_id: str | None = None


class MembershipOut(BaseModel):
    id: str
    user_id: str
    school_id: str
    role: SchoolRole
    class_id: str | None
    # True if this call created the membership; False if it already existed
    # (idempotent re-assign).
    created: bool


class CreateSessionRequest(BaseModel):
    student_id: str
    tier: CounselingTier
    notes: str = Field(default="", max_length=4000)


class CounselingSessionOut(BaseModel):
    id: str
    counselor_id: str
    student_id: str
    tier: CounselingTier
    notes: str


class CounselorProgressItemOut(BaseModel):
    """One competency's de-sensitized progress as a counselor sees it."""

    competency_id: str
    code: str
    area: CompetencyArea
    name_vi: str
    depth_achieved: Depth | None
    dev_phase: DevPhase


class DesensitizedAssessmentOut(BaseModel):
    """A de-sensitized assessment summary (instrument + derived code only)."""

    instrument_type: str
    summary_code: str | None

    @classmethod
    def from_model(cls, a: DesensitizedAssessment) -> DesensitizedAssessmentOut:
        return cls(instrument_type=a.instrument_type, summary_code=a.summary_code)


class StudentProgressOut(BaseModel):
    """A counselor's full de-sensitized view of a student (FR-82)."""

    student_id: str
    progress: list[CounselorProgressItemOut]
    assessments: list[DesensitizedAssessmentOut]

    @classmethod
    def from_view(cls, v: StudentProgressView) -> StudentProgressOut:
        return cls(
            student_id=v.student_id,
            progress=[
                CounselorProgressItemOut(
                    competency_id=item.competency.id,
                    code=item.competency.code,
                    area=item.competency.area,
                    name_vi=item.competency.name_vi,
                    depth_achieved=item.depth_achieved,
                    dev_phase=item.dev_phase,
                )
                for item in v.progress
            ],
            assessments=[DesensitizedAssessmentOut.from_model(a) for a in v.assessments],
        )
