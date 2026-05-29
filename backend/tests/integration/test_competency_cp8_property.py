"""CP-8 property test: depth_achieved is monotone under any advance sequence.

Mirrors tla/CompetencyProgress.tla ``Monotone``: for a (learner, competency),
``depth_achieved`` never decreases regardless of the order in which indicators
are recorded, and the append-only ``LearnerProgress`` history is preserved
(every successful advance leaves a row; no row is ever mutated or removed).
"""

from __future__ import annotations

import asyncio
import datetime

from app.auth.models import User
from app.auth.repository import SqlUserRepo
from app.competency.models import Competency, Indicator, LearnerProgress
from app.competency.repository import SqlCompetencyRepo
from app.competency.seed import seed_competencies
from app.competency.service import CompetencyService
from app.core.audit import SqlAuditRepo
from app.core.database import Base, Database
from app.core.enums import (
    AccountStatus,
    AgeBand,
    Depth,
    SchoolLevel,
    UserType,
    depth_rank,
)
from app.core.models import new_uuid
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# A random sequence of depths to record, in arbitrary order (with repeats).
_depth_sequences = st.lists(st.sampled_from(list(Depth)), min_size=1, max_size=25)


async def _reset_db(engine: AsyncEngine) -> Database:
    """Drop + recreate the schema on a shared engine, return a fresh Database view."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    database = Database.__new__(Database)
    database.engine = engine
    database.session_factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    return database


async def _seed_user_and_comp(db: Database) -> tuple[str, dict[Depth, str]]:
    uid = new_uuid()
    async with db.session_factory() as s:
        await seed_competencies(s)
        s.add(
            User(
                id=uid,
                email=f"{uid}@example.com",
                hashed_password="x",
                date_of_birth=datetime.date(2005, 1, 1),
                age_band=AgeBand.ADULT,
                user_type=UserType.STUDENT,
                school_level=SchoolLevel.UPPER_SECONDARY,
                account_status=AccountStatus.ACTIVE,
            )
        )
        await s.commit()
        comp = (
            (await s.execute(select(Competency).where(Competency.code == "NL1"))).scalars().first()
        )
        assert comp is not None
        inds = (
            (await s.execute(select(Indicator).where(Indicator.competency_id == comp.id)))
            .scalars()
            .all()
        )
        ind_by_depth = {i.depth: i.id for i in inds}
    return uid, ind_by_depth


async def _run_sequence(engine: AsyncEngine, depths: list[Depth]) -> None:
    db = await _reset_db(engine)
    uid, ind_by_depth = await _seed_user_and_comp(db)
    observed_max = 0
    advances = 0
    async with db.session_factory() as s:
        svc = CompetencyService(
            competencies=SqlCompetencyRepo(s),
            users=SqlUserRepo(s),
            audit=SqlAuditRepo(s),
        )
        for depth in depths:
            out = await svc.record_indicator(user_id=uid, indicator_id=ind_by_depth[depth])
            current = depth_rank(out.depth_achieved) if out.depth_achieved else 0
            # CP-8 monotonicity: current depth never drops below the prior max.
            assert current >= observed_max
            observed_max = max(observed_max, current)
            if out.advanced:
                advances += 1
        await s.commit()

    # Append-only: every advance left exactly one row; none mutated/removed.
    async with db.session_factory() as s:
        rows = (
            (await s.execute(select(LearnerProgress).where(LearnerProgress.user_id == uid)))
            .scalars()
            .all()
        )
    assert len(rows) == advances
    # Final stored max equals the highest depth requested in the sequence.
    expected_max = max(depth_rank(d) for d in depths)
    assert max((depth_rank(r.depth_achieved) for r in rows), default=0) == expected_max


def test_depth_is_monotone_under_random_advances() -> None:
    """CP-8 monotonicity over many random advance sequences.

    All Hypothesis examples run inside ONE event loop (a single
    ``asyncio.Runner``) sharing ONE in-memory engine whose schema is reset per
    example, so the aiosqlite background thread is created and disposed cleanly
    while the loop is open — never a fresh ``asyncio.run`` per example, which
    would race loop teardown against aiosqlite finalizers.
    """
    with asyncio.Runner() as runner:
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

        @settings(max_examples=60, deadline=None, suppress_health_check=[HealthCheck.too_slow])
        @given(depths=_depth_sequences)
        def _prop(depths: list[Depth]) -> None:
            runner.run(_run_sequence(engine, depths))

        try:
            _prop()
        finally:
            runner.run(engine.dispose())
