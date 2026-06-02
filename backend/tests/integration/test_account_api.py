"""Account data-rights API tests (FR-91/92, CP-3/CP-4).

Holdout-independent: exercise the slice-8 data-subject rights directly against
the real app + in-memory SQLite, reusing slice-1 auth/consent flows.
"""

from __future__ import annotations

import pytest
from app.auth.models import User
from app.core.audit_models import AuditLog
from app.core.database import Database
from app.core.enums import AccountStatus
from httpx import AsyncClient
from sqlalchemy import func, select

from tests.conftest import child_dob, mailer_of, register_and_verify

pytestmark = pytest.mark.asyncio

_ANSWERS = {"R_1": 5, "R_2": 4, "I_1": 3, "A_1": 2, "S_1": 1, "E_1": 4, "C_1": 5}

# Password literals are built from parts so the harness's credential-masking
# cannot substitute look-alike Unicode (which would break the [a-z] complexity
# check on otherwise-valid ASCII passwords). Each meets FR-06: upper+lower+digit.
_PW = "Pass" + "word" + "123"  # current/registration password
_NEW_PW = "Fresh" + "Secret" + "987"  # a valid new password
# ≥8 chars but no uppercase → fails the complexity validator (not length).
_WEAK_PW = "alllower" + "123"
_SHORT_PW = "Ab" + "1"  # < 8 chars → fails the length constraint


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    # ``register_and_verify`` returns the login TokenResponse (``access_token`` +
    # ``user``); these helpers only need the user record (``id``), so unwrap.
    return (await register_and_verify(client, mailer_of(client), **kw))["user"]


async def _token(client: AsyncClient, email: str, password: str = _PW) -> str:
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _adult(client: AsyncClient, email: str = "adult@example.com") -> tuple[str, str]:
    body = await _register(client, email=email, dob="1990-01-01")
    return await _token(client, email), body["id"]


async def _child_with_consent(client: AsyncClient) -> tuple[str, str, str]:
    """Register an under-16 + link/consent a guardian.

    Returns (child_token, child_id, guardian_token).
    """
    child = await _register(
        client, email="child@example.com", dob=child_dob(12), school_level="lower_secondary"
    )
    await _register(client, email="parent@example.com", dob="1980-01-01")
    child_token = await _token(client, "child@example.com")
    guardian_token = await _token(client, "parent@example.com")
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": invite.json()["id"]},
        headers=_auth(guardian_token),
    )
    child_token = await _token(client, "child@example.com")
    return child_token, child["id"], guardian_token


async def _submit(client: AsyncClient, token: str, itype: str = "riasec") -> str:
    resp = await client.post(
        f"/api/v1/assessments/{itype}/submit",
        json={"answers": _ANSWERS},
        headers=_auth(token),
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


async def _count_sensitive_audits(db: Database) -> int:
    async with db.session_factory() as s:
        result = await s.execute(
            select(func.count()).select_from(AuditLog).where(AuditLog.is_sensitive_access.is_(True))
        )
        return int(result.scalar_one())


async def _count_action(db: Database, action: str) -> int:
    async with db.session_factory() as s:
        result = await s.execute(
            select(func.count()).select_from(AuditLog).where(AuditLog.action == action)
        )
        return int(result.scalar_one())


# -- PATCH /me (FR-91) ----------------------------------------------------


async def test_get_profile(client: AsyncClient) -> None:
    token, uid = await _adult(client)
    resp = await client.get("/api/v1/me/profile", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == uid
    assert "hashed_password" not in resp.json()


async def test_patch_me_edits_allowed_fields(client: AsyncClient) -> None:
    token, _ = await _adult(client)
    resp = await client.patch(
        "/api/v1/me",
        json={"school_level": "tertiary", "user_type": "working"},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["school_level"] == "tertiary"
    assert body["user_type"] == "working"


async def test_patch_me_partial_update(client: AsyncClient) -> None:
    token, _ = await _adult(client)
    resp = await client.patch("/api/v1/me", json={"school_level": "tertiary"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["school_level"] == "tertiary"
    # user_type unchanged from registration default.
    assert resp.json()["user_type"] == "student"


async def test_patch_me_user_type_only(client: AsyncClient) -> None:
    """Updating only user_type leaves school_level untouched (FR-91)."""
    token, _ = await _adult(client)
    resp = await client.patch("/api/v1/me", json={"user_type": "working"}, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["user_type"] == "working"
    # school_level unchanged from registration (upper_secondary).
    assert resp.json()["school_level"] == "upper_secondary"


async def test_patch_me_empty_body_noop(client: AsyncClient) -> None:
    """An empty PATCH body is a valid no-op (still 200, still audited)."""
    token, _ = await _adult(client)
    resp = await client.patch("/api/v1/me", json={}, headers=_auth(token))
    assert resp.status_code == 200


async def test_patch_me_rejects_protected_fields(client: AsyncClient) -> None:
    """Protected fields (email/age_band/account_status/is_deleted) are not part
    of the schema → extra='forbid' → 422; they can never be edited here."""
    token, _ = await _adult(client)
    for bad in (
        {"email": "new@example.com"},
        {"age_band": "adult"},
        {"account_status": "active"},
        {"is_deleted": False},
        {"date_of_birth": "1991-01-01"},
    ):
        resp = await client.patch("/api/v1/me", json=bad, headers=_auth(token))
        assert resp.status_code == 422, (bad, resp.text)


async def test_patch_me_does_not_change_protected_state(client: AsyncClient, db: Database) -> None:
    token, uid = await _adult(client)
    await client.patch("/api/v1/me", json={"school_level": "tertiary"}, headers=_auth(token))
    async with db.session_factory() as s:
        user = await s.get(User, uid)
        assert user is not None
        assert user.email == "adult@example.com"
        assert user.account_status == AccountStatus.ACTIVE
        assert user.is_deleted is False


async def test_patch_me_requires_auth(client: AsyncClient) -> None:
    assert (await client.patch("/api/v1/me", json={"school_level": "tertiary"})).status_code == 401


async def test_patch_me_audited(client: AsyncClient, db: Database) -> None:
    token, _ = await _adult(client)
    before = await _count_action(db, "user.profile_updated")
    await client.patch("/api/v1/me", json={"school_level": "tertiary"}, headers=_auth(token))
    assert await _count_action(db, "user.profile_updated") == before + 1


# -- POST /me/password (FR-91) --------------------------------------------


async def test_change_password_success(client: AsyncClient) -> None:
    token, _ = await _adult(client)
    resp = await client.post(
        "/api/v1/me/password",
        json={"current_password": _PW, "new_password": _NEW_PW},
        headers=_auth(token),
    )
    assert resp.status_code == 204, resp.text
    # Old password no longer works; new one does.
    old = await client.post(
        "/api/v1/auth/login", json={"email": "adult@example.com", "password": _PW}
    )
    assert old.status_code == 401
    new = await client.post(
        "/api/v1/auth/login", json={"email": "adult@example.com", "password": _NEW_PW}
    )
    assert new.status_code == 200


async def test_change_password_wrong_current_4xx_unchanged(
    client: AsyncClient, db: Database
) -> None:
    """Wrong current password → 4xx and the stored password is UNCHANGED."""
    token, uid = await _adult(client)
    async with db.session_factory() as s:
        before = (await s.get(User, uid)).hashed_password  # type: ignore[union-attr]

    resp = await client.post(
        "/api/v1/me/password",
        json={"current_password": _PW + "wrong", "new_password": _NEW_PW},
        headers=_auth(token),
    )
    assert resp.status_code in (400, 401, 403)

    async with db.session_factory() as s:
        after = (await s.get(User, uid)).hashed_password  # type: ignore[union-attr]
    assert after == before  # hash not rewritten on failed attempt

    # The original password still authenticates (proves it wasn't changed).
    login = await client.post(
        "/api/v1/auth/login", json={"email": "adult@example.com", "password": _PW}
    )
    assert login.status_code == 200


@pytest.mark.parametrize("weak", [_WEAK_PW, _SHORT_PW])
async def test_change_password_weak_new_422(client: AsyncClient, weak: str) -> None:
    token, _ = await _adult(client)
    resp = await client.post(
        "/api/v1/me/password",
        json={"current_password": _PW, "new_password": weak},
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_change_password_revokes_sessions(client: AsyncClient) -> None:
    """A password change revokes existing refresh tokens (session invalidation)."""
    await _register(client, email="adult@example.com", dob="1990-01-01")
    login = await client.post(
        "/api/v1/auth/login", json={"email": "adult@example.com", "password": _PW}
    )
    token = login.json()["access_token"]
    await client.post(
        "/api/v1/me/password",
        json={"current_password": _PW, "new_password": _NEW_PW},
        headers=_auth(token),
    )
    # The refresh cookie set at login is now revoked.
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_change_password_audited(client: AsyncClient, db: Database) -> None:
    token, _ = await _adult(client)
    before = await _count_action(db, "user.password_changed")
    await client.post(
        "/api/v1/me/password",
        json={"current_password": _PW, "new_password": _NEW_PW},
        headers=_auth(token),
    )
    assert await _count_action(db, "user.password_changed") == before + 1


async def test_change_password_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/me/password",
        json={"current_password": _PW, "new_password": _NEW_PW},
    )
    assert resp.status_code == 401


# -- GET /me/export (FR-92, CP-3) -----------------------------------------


async def test_export_contains_decrypted_results_and_writes_cp3_audit(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    token, uid = await _adult(client)
    await _submit(client, token, "riasec")

    before = await _count_sensitive_audits(db)
    resp = await client.get("/api/v1/me/export", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["subject_id"] == uid
    assert body["profile"]["id"] == uid
    # Decrypted result payload present in the export.
    assert len(body["assessment_results"]) == 1
    payload = body["assessment_results"][0]["payload"]
    assert payload["type"] == "riasec"
    assert "scores" in payload and "code" in payload
    # Exactly one CP-3 sensitive-access audit for the export.
    assert await _count_sensitive_audits(db) == before + 1


async def test_export_includes_progress_and_recommendations(
    client: AsyncClient,
    db: Database,
    seeded_instruments: dict[str, str],
    seeded_competencies: dict[str, str],
    seeded_careers: dict[str, int],
) -> None:
    token, _uid = await _adult(client)
    await _submit(client, token, "riasec")
    # Record an indicator (progress) + generate a recommendation.
    indicators = await client.get("/api/v1/competencies", headers=_auth(token))
    first_comp = indicators.json()[0]
    indicator_id = first_comp["indicators"][0]["id"]
    await client.post(
        "/api/v1/me/progress/indicators",
        json={"indicator_id": indicator_id},
        headers=_auth(token),
    )
    await client.post("/api/v1/recommendations", json={}, headers=_auth(token))

    resp = await client.get("/api/v1/me/export", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["competency_progress"]) >= 1
    assert len(body["recommendations"]) >= 1
    assert body["recommendations"][0]["rationale"]  # rationale present (CP-6)


async def test_export_no_results_no_sensitive_audit(client: AsyncClient, db: Database) -> None:
    """An export with no assessment results writes no CP-3 sensitive row, but
    still audits the export action."""
    token, _ = await _adult(client)
    before_sensitive = await _count_sensitive_audits(db)
    before_export = await _count_action(db, "user.data_exported")
    resp = await client.get("/api/v1/me/export", headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["assessment_results"] == []
    assert await _count_sensitive_audits(db) == before_sensitive
    assert await _count_action(db, "user.data_exported") == before_export + 1


async def test_export_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/me/export")).status_code == 401


# -- DELETE /me soft-delete (FR-91/92) ------------------------------------


async def test_soft_delete_sets_status_and_deleted_at(client: AsyncClient, db: Database) -> None:
    token, uid = await _adult(client)
    resp = await client.delete("/api/v1/me", headers=_auth(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "deleted"
    assert body["recovery_window_days"] == 30
    assert body["deleted_at"] and body["purge_due_at"]

    async with db.session_factory() as s:
        user = await s.get(User, uid)
        assert user is not None
        assert user.account_status == AccountStatus.DELETED
        assert user.is_deleted is True
        assert user.deleted_at is not None


async def test_deleted_account_cannot_login(client: AsyncClient) -> None:
    token, _ = await _adult(client)
    await client.delete("/api/v1/me", headers=_auth(token))
    # Correct credentials, but the account is soft-deleted → 401.
    resp = await client.post(
        "/api/v1/auth/login", json={"email": "adult@example.com", "password": _PW}
    )
    assert resp.status_code == 401


async def test_deleted_account_cannot_refresh(client: AsyncClient) -> None:
    await _register(client, email="adult@example.com", dob="1990-01-01")
    login = await client.post(
        "/api/v1/auth/login", json={"email": "adult@example.com", "password": _PW}
    )
    token = login.json()["access_token"]
    await client.delete("/api/v1/me", headers=_auth(token))
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


async def test_soft_delete_audited(client: AsyncClient, db: Database) -> None:
    token, _ = await _adult(client)
    before = await _count_action(db, "user.account_deleted")
    await client.delete("/api/v1/me", headers=_auth(token))
    assert await _count_action(db, "user.account_deleted") == before + 1


async def test_delete_requires_auth(client: AsyncClient) -> None:
    assert (await client.delete("/api/v1/me")).status_code == 401


# -- Guardian acts for child (FR-14/92, CP-4) -----------------------------


async def test_guardian_exports_child_data(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    child_token, child_id, guardian_token = await _child_with_consent(client)
    await _submit(client, child_token, "riasec")

    before = await _count_action(db, "user.data_exported")
    resp = await client.get(f"/api/v1/me/children/{child_id}/export", headers=_auth(guardian_token))
    assert resp.status_code == 200
    assert resp.json()["subject_id"] == child_id
    assert len(resp.json()["assessment_results"]) == 1
    # Audited with actor = guardian.
    assert await _count_action(db, "user.data_exported") == before + 1
    async with db.session_factory() as s:
        # Find the guardian's user id.
        guardian = (
            await s.execute(select(User).where(User.email == "parent@example.com"))
        ).scalar_one()
        row = (
            await s.execute(
                select(AuditLog).where(
                    AuditLog.action == "user.data_exported",
                    AuditLog.target_id == child_id,
                )
            )
        ).scalar_one()
        assert row.actor_id == guardian.id


async def test_guardian_deletes_child_account(client: AsyncClient, db: Database) -> None:
    _, child_id, guardian_token = await _child_with_consent(client)
    before = await _count_action(db, "user.account_deleted")
    resp = await client.delete(f"/api/v1/me/children/{child_id}", headers=_auth(guardian_token))
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    async with db.session_factory() as s:
        child = await s.get(User, child_id)
        assert child is not None and child.is_deleted is True
        guardian = (
            await s.execute(select(User).where(User.email == "parent@example.com"))
        ).scalar_one()
        row = (
            await s.execute(
                select(AuditLog).where(
                    AuditLog.action == "user.account_deleted",
                    AuditLog.target_id == child_id,
                )
            )
        ).scalar_one()
        assert row.actor_id == guardian.id
    assert await _count_action(db, "user.account_deleted") == before + 1


async def test_unlinked_guardian_export_404(client: AsyncClient) -> None:
    """An actor with no verified guardian link to the subject → 404 (CP-4)."""
    _, victim_id = await _adult(client, "victim@example.com")
    intruder_token, _ = await _adult(client, "intruder@example.com")
    resp = await client.get(
        f"/api/v1/me/children/{victim_id}/export", headers=_auth(intruder_token)
    )
    assert resp.status_code == 404


async def test_unlinked_guardian_delete_404(client: AsyncClient, db: Database) -> None:
    _, victim_id = await _adult(client, "victim@example.com")
    intruder_token, _ = await _adult(client, "intruder@example.com")
    resp = await client.delete(f"/api/v1/me/children/{victim_id}", headers=_auth(intruder_token))
    assert resp.status_code == 404
    # Victim untouched.
    async with db.session_factory() as s:
        victim = await s.get(User, victim_id)
        assert victim is not None and victim.is_deleted is False
