"""CompetencyService tests against the real repo + in-memory DB.

Covers CP-8 (depth only advances; append-only history), dev_phase resolution
(inferred for students, stored-row override / deviation, working multi-phase),
and the NotFound error paths.
"""

from __future__ import annotations

import pytest
from app.auth.models import User
from app.auth.repository import SqlUserRepo
from app.competency.models import Competency, Indicator, LearnerProgress
from app.competency.repository import SqlCompetencyRepo
from app.competency.service import CompetencyService
from app.core.audit import SqlAuditRepo
from app.core.database import Database
from app.core.enums import (
    AccountStatus,
    AgeBand,
    CompetencyArea,
    Depth,
    DevPhase,
    SchoolLevel,
    UserType,
)
from app.core.exceptions import NotFoundError
from app.core.models import new_uuid
from sqlalchemy import func, select

pytestmark = pytest.mark.asyncio


async def _make_user(
    db: Database,
    *,
    user_type: UserType = UserType.STUDENT,
    school_level: SchoolLevel = SchoolLevel.UPPER_SECONDARY,
) -> str:
    uid = new_uuid()
    async with db.session_factory() as s:
        s.add(
            User(
                id=uid,
                email=f"{uid}@example.com",
                hashed_password="x",
                date_of_birth=__import__("datetime").date(2005, 1, 1),
                age_band=AgeBand.ADULT,
                user_type=user_type,
                school_level=school_level,
                account_status=AccountStatus.ACTIVE,
            )
        )
        await s.commit()
    return uid


def _service(s) -> CompetencyService:  # type: ignore[no-untyped-def]
    return CompetencyService(
        competencies=SqlCompetencyRepo(s),
        users=SqlUserRepo(s),
        audit=SqlAuditRepo(s),
    )


async def _indicator(s, code: str, depth: Depth) -> Indicator:  # type: ignore[no-untyped-def]
    """Resolve the indicator at ``depth`` for the competency with ``code``."""
    comp = (await s.execute(select(Competency).where(Competency.code == code))).scalars().first()
    assert comp is not None
    ind = (
        (
            await s.execute(
                select(Indicator).where(
                    Indicator.competency_id == comp.id, Indicator.depth == depth
                )
            )
        )
        .scalars()
        .first()
    )
    assert ind is not None
    return ind


async def test_list_tree_returns_twelve_with_indicators(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    async with db.session_factory() as s:
        comps, by_comp = await _service(s).list_tree()
    assert len(comps) == 12
    assert all(len(by_comp[c.id]) == 3 for c in comps)


async def test_record_indicator_advances_then_holds(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    uid = await _make_user(db)
    async with db.session_factory() as s:
        svc = _service(s)
        ind_k = await _indicator(s, "NL1", Depth.K)
        ind_a = await _indicator(s, "NL1", Depth.A)
        ind_r = await _indicator(s, "NL1", Depth.R)

        out_k = await svc.record_indicator(user_id=uid, indicator_id=ind_k.id)
        assert out_k.advanced is True and out_k.depth_achieved == Depth.K

        out_a = await svc.record_indicator(user_id=uid, indicator_id=ind_a.id)
        assert out_a.advanced is True and out_a.depth_achieved == Depth.A

        # Re-recording a lower depth must NOT regress (CP-8).
        out_k2 = await svc.record_indicator(user_id=uid, indicator_id=ind_k.id)
        assert out_k2.advanced is False and out_k2.depth_achieved == Depth.A

        # Same depth again: no advance, no duplicate.
        out_a2 = await svc.record_indicator(user_id=uid, indicator_id=ind_a.id)
        assert out_a2.advanced is False and out_a2.depth_achieved == Depth.A

        out_r = await svc.record_indicator(user_id=uid, indicator_id=ind_r.id)
        assert out_r.advanced is True and out_r.depth_achieved == Depth.R
        await s.commit()

    # History preserved (append-only): exactly 3 rows written (K, A, R).
    async with db.session_factory() as s:
        n = int(
            (
                await s.execute(
                    select(func.count())
                    .select_from(LearnerProgress)
                    .where(LearnerProgress.user_id == uid)
                )
            ).scalar_one()
        )
    assert n == 3


async def test_record_unknown_indicator_404(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    uid = await _make_user(db)
    async with db.session_factory() as s:
        with pytest.raises(NotFoundError):
            await _service(s).record_indicator(user_id=uid, indicator_id="nope")


async def test_get_progress_unknown_user_404(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    async with db.session_factory() as s:
        with pytest.raises(NotFoundError):
            await _service(s).get_progress(user_id="ghost")


async def test_get_progress_student_infers_phase(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    uid = await _make_user(db, school_level=SchoolLevel.LOWER_SECONDARY)
    async with db.session_factory() as s:
        items = await _service(s).get_progress(user_id=uid)
    assert len(items) == 12
    # No progress yet → depth None; THCS student → exploration everywhere.
    assert all(i.depth_achieved is None for i in items)
    assert all(i.dev_phase == DevPhase.EXPLORATION for i in items)


async def test_stored_phase_overrides_inference_deviation(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    """A stored LearnerDomainPhase row beats the school-level inference (deviation)."""
    uid = await _make_user(db, school_level=SchoolLevel.LOWER_SECONDARY)
    async with db.session_factory() as s:
        svc = _service(s)
        # Student deviates: set A_personal to planning despite THCS default.
        await svc.set_domain_phase(
            user_id=uid, area=CompetencyArea.A_PERSONAL, dev_phase=DevPhase.PLANNING
        )
        await s.commit()
    async with db.session_factory() as s:
        items = await _service(s).get_progress(user_id=uid)
    by_area = {i.competency.area: i.dev_phase for i in items}
    assert by_area[CompetencyArea.A_PERSONAL] == DevPhase.PLANNING  # deviation honoured
    assert by_area[CompetencyArea.B_EXPLORATION] == DevPhase.EXPLORATION  # still inferred


async def test_working_user_multiple_phases_by_area(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    """Working users hold several phases at once (one per area), no inference."""
    uid = await _make_user(db, user_type=UserType.WORKING, school_level=SchoolLevel.NONE)
    async with db.session_factory() as s:
        svc = _service(s)
        await svc.set_domain_phase(
            user_id=uid, area=CompetencyArea.A_PERSONAL, dev_phase=DevPhase.PLANNING
        )
        await svc.set_domain_phase(
            user_id=uid, area=CompetencyArea.B_EXPLORATION, dev_phase=DevPhase.AWARENESS
        )
        await s.commit()
    async with db.session_factory() as s:
        items = await _service(s).get_progress(user_id=uid)
    by_area = {i.competency.area: i.dev_phase for i in items}
    assert by_area[CompetencyArea.A_PERSONAL] == DevPhase.PLANNING
    assert by_area[CompetencyArea.B_EXPLORATION] == DevPhase.AWARENESS
    # C_building has no stored row and user is working → safe default awareness.
    assert by_area[CompetencyArea.C_BUILDING] == DevPhase.AWARENESS


async def test_latest_stored_phase_wins(db: Database, seeded_competencies: dict[str, str]) -> None:
    """Multiple rows for the same area: the latest set_at is the phase in force."""
    uid = await _make_user(db, user_type=UserType.WORKING, school_level=SchoolLevel.NONE)
    async with db.session_factory() as s:
        svc = _service(s)
        await svc.set_domain_phase(
            user_id=uid, area=CompetencyArea.A_PERSONAL, dev_phase=DevPhase.AWARENESS
        )
        await svc.set_domain_phase(
            user_id=uid, area=CompetencyArea.A_PERSONAL, dev_phase=DevPhase.PLANNING
        )
        await s.commit()
    async with db.session_factory() as s:
        items = await _service(s).get_progress(user_id=uid)
    by_area = {i.competency.area: i.dev_phase for i in items}
    assert by_area[CompetencyArea.A_PERSONAL] == DevPhase.PLANNING


async def test_progress_reflects_recorded_depth(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    uid = await _make_user(db)
    async with db.session_factory() as s:
        svc = _service(s)
        ind_a = await _indicator(s, "NL5", Depth.A)
        await svc.record_indicator(user_id=uid, indicator_id=ind_a.id)
        await s.commit()
    async with db.session_factory() as s:
        items = await _service(s).get_progress(user_id=uid)
    by_code = {i.competency.code: i.depth_achieved for i in items}
    assert by_code["NL5"] == Depth.A
    assert by_code["NL1"] is None


async def test_current_depth_is_max_regardless_of_row_order(
    db: Database, seeded_competencies: dict[str, str]
) -> None:
    """`get_progress` reports the MAX attained depth even if a lower-depth row
    was appended after a higher one (history is append-only; max wins, CP-8)."""
    uid = await _make_user(db)
    async with db.session_factory() as s:
        comp = (
            (await s.execute(select(Competency).where(Competency.code == "NL1"))).scalars().first()
        )
        assert comp is not None
        # Insert R first, then K (out of advance order) directly into the table.
        for depth in (Depth.R, Depth.K):
            s.add(
                LearnerProgress(
                    id=new_uuid(),
                    user_id=uid,
                    competency_id=comp.id,
                    depth_achieved=depth,
                    evidence_ref="test",
                )
            )
        await s.commit()
    async with db.session_factory() as s:
        items = await _service(s).get_progress(user_id=uid)
    by_code = {i.competency.code: i.depth_achieved for i in items}
    assert by_code["NL1"] == Depth.R  # max retained, not the last-inserted K
