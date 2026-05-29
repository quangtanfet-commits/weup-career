"""RecoService tests: CP-6 guard, DB NOT NULL, audit (FR-63), profile build.

These go through the real repos + session (not HTTP) so we can assert the
storage-layer invariants and the audit side effects directly.
"""

from __future__ import annotations

import json

import pytest
from app.assessments.models import AssessmentResult
from app.competency.models import LearnerProgress
from app.core.audit import SqlAuditRepo
from app.core.crypto import FieldCrypto
from app.core.enums import Depth, RecoDecision
from app.core.exceptions import RationaleRequiredError
from app.core.models import new_uuid
from app.reco.repository import SqlRecoRepo
from app.reco.service import RecoService
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import make_settings

pytestmark = pytest.mark.asyncio


def _service(session: AsyncSession) -> tuple[RecoService, SqlAuditRepo, FieldCrypto]:
    crypto = FieldCrypto(make_settings().field_encryption_key)
    audit = SqlAuditRepo(session)
    svc = RecoService(reco=SqlRecoRepo(session), audit=audit, crypto=crypto)
    return svc, audit, crypto


async def _make_user(session: AsyncSession, email: str = "u@example.com") -> str:
    from datetime import date

    from app.auth.models import User
    from app.core.enums import AccountStatus, AgeBand, SchoolLevel, UserType

    uid = new_uuid()
    session.add(
        User(
            id=uid,
            email=email,
            hashed_password="x",
            date_of_birth=date(1990, 1, 1),
            age_band=AgeBand.ADULT,
            user_type=UserType.STUDENT,
            school_level=SchoolLevel.UPPER_SECONDARY,
            account_status=AccountStatus.ACTIVE,
        )
    )
    await session.flush()
    return uid


async def test_generate_persists_proposed_with_audit(
    session: AsyncSession, seeded_careers: dict[str, int]
) -> None:
    """FR-63 + CP-5: generate writes a proposed reco and an audit row."""
    svc, audit, _ = _service(session)
    uid = await _make_user(session)

    reco = await svc.generate(user_id=uid)
    assert reco.requires_human_confirmation is True
    assert reco.confirmed_by is None
    assert reco.confirmed_decision is None
    assert reco.rationale.strip()

    # FR-63: an audit row records the recommendation creation.
    count = await session.execute(
        select(func.count()).select_from(
            __import__("app.core.audit_models", fromlist=["AuditLog"]).AuditLog
        )
    )
    assert int(count.scalar_one()) >= 1


async def test_generate_builds_profile_from_results_and_progress(
    session: AsyncSession,
    seeded_careers: dict[str, int],
    seeded_instruments: dict[str, str],
    seeded_competencies: dict[str, str],
) -> None:
    """The profile reflects the user's RIASEC result + competency depth (matched careers)."""
    svc, _, crypto = _service(session)
    uid = await _make_user(session)

    # A RIASEC result whose Holland code leads with I,R (→ software engineer).
    payload = {"type": "riasec", "scores": {"I": 10, "R": 8}, "code": "IRA"}
    session.add(
        AssessmentResult(
            id=new_uuid(),
            user_id=uid,
            instrument_id=seeded_instruments["riasec"],
            result_payload=crypto.encrypt(json.dumps(payload)),
            key_version=crypto.key_version,
            is_sensitive=True,
            version=1,
        )
    )
    # Competency depth on NL5 (required by the software career).
    session.add(
        LearnerProgress(
            id=new_uuid(),
            user_id=uid,
            competency_id=seeded_competencies["NL5"],
            depth_achieved=Depth.A,
        )
    )
    await session.flush()

    reco = await svc.generate(user_id=uid)
    careers = reco.payload["careers"]
    assert careers, "expected at least one ranked career"
    # The matched RIASEC letters should appear for the top career.
    top = careers[0]
    assert top["matched_riasec"], top
    # NL5 evidence influenced at least one career's match set.
    assert any("NL5" in c["matched_competencies"] for c in careers)


async def test_generate_rejects_empty_rationale_cp6(
    session: AsyncSession, seeded_careers: dict[str, int], monkeypatch: pytest.MonkeyPatch
) -> None:
    """CP-6 service guard: an empty rationale is refused before persisting."""
    svc, _, _ = _service(session)
    uid = await _make_user(session)

    from app.reco import service as service_mod
    from app.reco.engine import RecoResult

    def _blank(*args: object, **kwargs: object) -> RecoResult:
        return RecoResult(careers=(), pathway=None, rationale="   ")

    monkeypatch.setattr(service_mod, "recommend", _blank)

    with pytest.raises(RationaleRequiredError):
        await svc.generate(user_id=uid)

    # Nothing was persisted (guard fired before add).
    from app.reco.models import Recommendation

    count = await session.execute(select(func.count()).select_from(Recommendation))
    assert int(count.scalar_one()) == 0


async def test_db_rejects_null_rationale_cp6(
    session: AsyncSession, seeded_careers: dict[str, int]
) -> None:
    """CP-6 storage layer: the DB column itself forbids a NULL rationale."""
    import sqlalchemy.exc
    from app.reco.models import Recommendation

    uid = await _make_user(session)
    session.add(
        Recommendation(
            id=new_uuid(),
            user_id=uid,
            payload={},
            rationale=None,  # type: ignore[arg-type]
        )
    )
    with pytest.raises(sqlalchemy.exc.IntegrityError):
        await session.flush()
    # Leave the session usable for fixture teardown (commit-on-exit).
    await session.rollback()


async def test_confirm_sets_decision_and_audits(
    session: AsyncSession, seeded_careers: dict[str, int]
) -> None:
    """confirm records the human decision + an audit row (FR-63, CP-5)."""
    svc, _, _ = _service(session)
    uid = await _make_user(session)
    reco = await svc.generate(user_id=uid)

    confirmed = await svc.confirm(user_id=uid, reco_id=reco.id, decision=RecoDecision.ACCEPTED)
    assert confirmed.confirmed_by == uid
    assert confirmed.confirmed_decision == RecoDecision.ACCEPTED

    from app.core.audit_models import AuditLog

    rows = await session.execute(
        select(AuditLog).where(AuditLog.action == "recommendation.confirmed")
    )
    assert rows.scalars().first() is not None


async def test_get_owned_cross_user_not_found(
    session: AsyncSession, seeded_careers: dict[str, int]
) -> None:
    """CP-4: get_owned never returns another user's reco."""
    from app.core.exceptions import NotFoundError

    svc, _, _ = _service(session)
    owner = await _make_user(session, email="owner@example.com")
    reco = await svc.generate(user_id=owner)

    other = await _make_user(session, email="other@example.com")
    with pytest.raises(NotFoundError):
        await svc.get_for_actor(user_id=other, reco_id=reco.id)


async def test_get_owned_happy_path(session: AsyncSession, seeded_careers: dict[str, int]) -> None:
    """The owner can fetch their own recommendation (CP-4 positive case)."""
    svc, _, _ = _service(session)
    uid = await _make_user(session)
    reco = await svc.generate(user_id=uid)
    fetched = await svc.get_for_actor(user_id=uid, reco_id=reco.id)
    assert fetched.id == reco.id


async def test_get_for_actor_guardian_path_without_counselor_hook(
    session: AsyncSession, seeded_careers: dict[str, int]
) -> None:
    """G-6: with guardians wired but NO counselor hook, the guardian path works.

    Builds the service with ``guardians`` set and ``counselor_access=None`` so
    ``_counselor_check_adapter`` returns None — exercising the guardian-only
    relational branch of ``can_access``.
    """
    from datetime import UTC, datetime

    from app.core.enums import VerificationMethod
    from app.guardians.models import GuardianLink
    from app.guardians.repository import SqlGuardianRepo

    crypto = FieldCrypto(make_settings().field_encryption_key)
    audit = SqlAuditRepo(session)
    guardians = SqlGuardianRepo(session)
    svc = RecoService(
        reco=SqlRecoRepo(session),
        audit=audit,
        crypto=crypto,
        guardians=guardians,
        counselor_access=None,
    )
    child = await _make_user(session, email="child2@example.com")
    guardian = await _make_user(session, email="guardian2@example.com")
    session.add(
        GuardianLink(
            id=new_uuid(),
            child_user_id=child,
            guardian_user_id=guardian,
            relationship="mother",
            verified_at=datetime.now(UTC),
            verification_method=VerificationMethod.EMAIL,
        )
    )
    await session.flush()
    reco = await svc.generate(user_id=child)

    fetched = await svc.get_for_actor(user_id=guardian, reco_id=reco.id)
    assert fetched.id == reco.id
    confirmed = await svc.confirm(user_id=guardian, reco_id=reco.id, decision=RecoDecision.ACCEPTED)
    assert confirmed.confirmed_by == guardian  # CP-5: the real human


async def test_repo_get_by_id(session: AsyncSession, seeded_careers: dict[str, int]) -> None:
    """``SqlRecoRepo.get_by_id`` returns a stored reco (and None for unknown)."""
    svc, _, _ = _service(session)
    repo = SqlRecoRepo(session)
    uid = await _make_user(session)
    reco = await svc.generate(user_id=uid)
    assert (await repo.get_by_id(reco.id)) is not None
    assert (await repo.get_by_id("nope")) is None
