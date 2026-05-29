"""School-channel HTTP routes (spec.md §6, FR-80..83, CP-3/CP-4).

- ``GET /school/{school_id}/students`` — Bearer + (school_admin OR counselor of
  that school). Returns the school-scoped roster; an actor without a staff
  membership in that school (incl. a counselor of a different school) gets 404
  (existence-hiding, auth-design.md).
- ``POST /counseling/sessions`` — Bearer + counselor. Records a Tier 1/2/3
  session for a student the counselor is authorised for (CP-4); an unauthorised
  student → 404. Audited.
- ``GET /school/students/{student_id}/progress`` — Bearer + counselor (or other
  authorised relation). De-sensitized competency progress + assessment summary
  (FR-82); raw encrypted payload is NEVER returned (FR-83, NFR-10). Every read
  writes a CP-3 sensitive-access audit row.

These are relational-RBAC routes (CP-4); they are not under the under-16 consent
gate — they are a different human (counselor/guardian) accessing an authorised
student's data, which the relational ``can_access`` governs.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, status

from app.api.deps import CurrentUser, get_current_user, school_service
from app.school.schemas import (
    AssignMemberRequest,
    CounselingSessionOut,
    CreateClassRequest,
    CreateSessionRequest,
    MembershipOut,
    RosterEntryOut,
    SchoolClassOut,
    StudentProgressOut,
)
from app.school.service import SchoolService

router = APIRouter(tags=["school"])


# -- school_admin write CRUD (FR-80, G-7) ---------------------------------
# Authorised to a school_admin OF the given school only; authority is
# re-derived from SchoolMembership (never the JWT). A non-admin, or an admin of
# another school, gets 404 (existence-hiding) — never crosses school boundaries.


@router.post(
    "/school/{school_id}/classes",
    response_model=SchoolClassOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_class(
    payload: CreateClassRequest,
    school_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: SchoolService = Depends(school_service),
) -> SchoolClassOut:
    klass = await service.create_class(
        actor_id=current.id, school_id=school_id, name=payload.name, grade=payload.grade
    )
    return SchoolClassOut.from_model(klass)


@router.get("/school/{school_id}/classes", response_model=list[SchoolClassOut])
async def list_classes(
    school_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: SchoolService = Depends(school_service),
) -> list[SchoolClassOut]:
    classes = await service.list_classes(actor_id=current.id, school_id=school_id)
    return [SchoolClassOut.from_model(k) for k in classes]


@router.post(
    "/school/{school_id}/members",
    response_model=MembershipOut,
    status_code=status.HTTP_201_CREATED,
)
async def assign_member(
    payload: AssignMemberRequest,
    school_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: SchoolService = Depends(school_service),
) -> MembershipOut:
    membership, created = await service.assign_member(
        actor_id=current.id,
        school_id=school_id,
        user_id=payload.user_id,
        role=payload.role,
        class_id=payload.class_id,
    )
    return MembershipOut(
        id=membership.id,
        user_id=membership.user_id,
        school_id=membership.school_id,
        role=membership.role,
        class_id=membership.class_id,
        created=created,
    )


@router.get("/school/{school_id}/students", response_model=list[RosterEntryOut])
async def list_school_students(
    school_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: SchoolService = Depends(school_service),
) -> list[RosterEntryOut]:
    entries = await service.list_students(actor_id=current.id, school_id=school_id)
    return [RosterEntryOut.from_entry(e) for e in entries]


@router.post(
    "/counseling/sessions",
    response_model=CounselingSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_counseling_session(
    payload: CreateSessionRequest,
    current: CurrentUser = Depends(get_current_user),
    service: SchoolService = Depends(school_service),
) -> CounselingSessionOut:
    session = await service.create_session(
        counselor_id=current.id,
        student_id=payload.student_id,
        tier=payload.tier,
        notes=payload.notes,
    )
    return CounselingSessionOut(
        id=session.id,
        counselor_id=session.counselor_id,
        student_id=session.student_id,
        tier=session.tier,
        notes=session.notes,
    )


@router.get(
    "/school/students/{student_id}/progress",
    response_model=StudentProgressOut,
)
async def read_student_progress(
    student_id: str = Path(...),
    current: CurrentUser = Depends(get_current_user),
    service: SchoolService = Depends(school_service),
) -> StudentProgressOut:
    view = await service.read_student_progress(counselor_id=current.id, student_id=student_id)
    return StudentProgressOut.from_view(view)
