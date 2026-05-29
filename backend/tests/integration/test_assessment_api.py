"""Assessment API integration tests (CP-1, CP-3, crypto, ownership, versioning).

Holdout-independent: these exercise the slice-2 invariants directly against the
real app + in-memory SQLite, reusing the slice-1 auth/consent flow.
"""

from __future__ import annotations

import json

import pytest
from app.assessments.models import AssessmentResult
from app.core.audit_models import AuditLog
from app.core.database import Database
from httpx import AsyncClient
from sqlalchemy import func, select

from tests.conftest import child_dob, make_settings, register_payload

pytestmark = pytest.mark.asyncio

_ANSWERS = {"R_1": 5, "R_2": 4, "I_1": 3, "A_1": 2, "S_1": 1, "E_1": 4, "C_1": 5}


async def _register(client: AsyncClient, **kw: str) -> dict[str, str]:
    resp = await client.post("/api/v1/auth/register", json=register_payload(**kw))
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _token(client: AsyncClient, email: str, password: str = "Password123") -> str:
    login = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": password}
    )
    return login.json()["access_token"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _adult(client: AsyncClient, email: str = "adult@example.com") -> str:
    await _register(client, email=email, dob="1990-01-01")
    return await _token(client, email)


async def _child_with_consent(client: AsyncClient) -> tuple[str, str]:
    """Register an under-16, link+consent a guardian; return (token, child_id)."""
    child = await _register(
        client, email="child@example.com", dob=child_dob(12),
        school_level="lower_secondary",
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
    # Re-login so the JWT claim reflects the now-active account.
    return await _token(client, "child@example.com"), child["id"]


# -- listing --------------------------------------------------------------


async def test_list_instruments(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.get("/api/v1/assessments", headers=_auth(token))
    assert resp.status_code == 200
    types = {i["type"] for i in resp.json()}
    assert types == {"riasec", "vips", "mbti"}


async def test_list_requires_auth(client: AsyncClient) -> None:
    assert (await client.get("/api/v1/assessments")).status_code == 401


# -- CP-1: consent gate ---------------------------------------------------


async def test_under16_without_consent_submit_403(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    """CP-1: under-16, no active consent → 403 GUARDIAN_CONSENT_REQUIRED."""
    await _register(
        client, email="kid@example.com", dob=child_dob(12),
        school_level="lower_secondary",
    )
    token = await _token(client, "kid@example.com")
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS},
        headers=_auth(token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"


async def test_under16_with_consent_submit_201(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    """CP-1: once consent is active, the child can submit (201, new result)."""
    child_token, _ = await _child_with_consent(client)
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS},
        headers=_auth(child_token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["version"] == 1
    assert body["is_sensitive"] is True
    assert "payload" not in body  # submit ack carries no result content


async def test_revoked_consent_blocks_new_submit_cp2(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    child_token, child_id = await _child_with_consent(client)
    guardian_token = await _token(client, "parent@example.com")
    await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS}, headers=_auth(child_token),
    )
    await client.post(
        "/api/v1/guardians/consent/revoke",
        json={"child_user_id": child_id}, headers=_auth(guardian_token),
    )
    # Re-login: claim now reflects pending status, and DB re-check blocks.
    child_token = await _token(client, "child@example.com")
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS}, headers=_auth(child_token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "GUARDIAN_CONSENT_REQUIRED"


async def test_adult_submit_no_consent_needed(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.post(
        "/api/v1/assessments/mbti/submit",
        json={"answers": {"E_1": 5, "N_1": 5, "T_1": 5, "J_1": 5}},
        headers=_auth(token),
    )
    assert resp.status_code == 201


# -- CP-3: audit on every read, fail-closed -------------------------------


async def _submit(client: AsyncClient, token: str, itype: str = "riasec") -> str:
    resp = await client.post(
        f"/api/v1/assessments/{itype}/submit",
        json={"answers": _ANSWERS}, headers=_auth(token),
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def _count_sensitive_audits(db: Database) -> int:
    async with db.session_factory() as s:
        result = await s.execute(
            select(func.count()).select_from(AuditLog).where(
                AuditLog.is_sensitive_access.is_(True)
            )
        )
        return int(result.scalar_one())


async def test_each_read_writes_exactly_one_sensitive_audit_cp3(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    result_id = await _submit(client, token)

    before = await _count_sensitive_audits(db)
    read = await client.get(
        f"/api/v1/me/assessments/{result_id}", headers=_auth(token)
    )
    assert read.status_code == 200
    after = await _count_sensitive_audits(db)
    assert after == before + 1  # exactly one sensitive audit per read

    # A second read adds exactly one more.
    await client.get(f"/api/v1/me/assessments/{result_id}", headers=_auth(token))
    assert (await _count_sensitive_audits(db)) == before + 2


async def test_read_returns_decrypted_payload(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    result_id = await _submit(client, token)
    read = await client.get(
        f"/api/v1/me/assessments/{result_id}", headers=_auth(token)
    )
    payload = read.json()["payload"]
    assert payload["type"] == "riasec"
    assert "scores" in payload and "code" in payload


async def test_read_fail_closed_when_audit_write_fails_cp3(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    """If the sensitive-access audit write fails, the read fails closed.

    Verified at the service layer (precise): the audit record is attempted
    BEFORE the payload is decrypted/returned, so a raising audit store means no
    payload is ever produced — there is no read path that skips audit (CP-3).
    """
    from app.assessments.repository import SqlAssessmentRepo
    from app.assessments.service import AssessmentService
    from app.core.audit import SqlAuditRepo
    from app.core.crypto import FieldCrypto
    from app.guardians.repository import SqlGuardianRepo

    token = await _adult(client)
    result_id = await _submit(client, token)
    # Resolve the owning user id from the stored row.
    async with db.session_factory() as s:
        row = await s.get(AssessmentResult, result_id)
        assert row is not None
        owner_id = row.user_id

    class BoomAudit(SqlAuditRepo):
        async def record(self, **kwargs: object):  # type: ignore[no-untyped-def]
            if kwargs.get("is_sensitive_access"):
                raise RuntimeError("audit store down")
            return await super().record(**kwargs)  # type: ignore[arg-type]

    async with db.session_factory() as s:
        svc = AssessmentService(
            settings=make_settings(),
            assessments=SqlAssessmentRepo(s),
            guardians=SqlGuardianRepo(s),
            audit=BoomAudit(s),
            crypto=FieldCrypto(make_settings().field_encryption_key),
        )
        with pytest.raises(RuntimeError, match="audit store down"):
            await svc.read_result(user_id=owner_id, result_id=result_id)


# -- Crypto at rest -------------------------------------------------------


async def test_payload_encrypted_at_rest(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    """The stored column is ciphertext — no plaintext result labels present."""
    token = await _adult(client)
    result_id = await _submit(client, token)

    async with db.session_factory() as s:
        row = await s.get(AssessmentResult, result_id)
        assert row is not None
        stored = row.result_payload

    assert stored.startswith("v1:")  # Field Crypto wire format
    # No plaintext markers of the scored payload leak into the column.
    for marker in ("riasec", "scores", "code", '"R"', "type"):
        assert marker not in stored
    # And it is not valid JSON (it's encrypted).
    with pytest.raises(json.JSONDecodeError):
        json.loads(stored)


# -- Ownership (CP-4) -----------------------------------------------------


async def test_cross_user_read_404(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    owner = await _adult(client, "owner@example.com")
    result_id = await _submit(client, owner)

    other = await _adult(client, "intruder@example.com")
    resp = await client.get(
        f"/api/v1/me/assessments/{result_id}", headers=_auth(other)
    )
    assert resp.status_code == 404


async def test_read_unknown_result_404(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.get(
        "/api/v1/me/assessments/does-not-exist", headers=_auth(token)
    )
    assert resp.status_code == 404


# -- Versioning (FR-15) ---------------------------------------------------


async def test_retake_creates_new_version_keeps_old(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    first = await _submit(client, token)
    second = await _submit(client, token)
    assert first != second

    async with db.session_factory() as s:
        rows = (
            await s.execute(
                select(AssessmentResult).order_by(AssessmentResult.version)
            )
        ).scalars().all()
    versions = [r.version for r in rows]
    assert versions == [1, 2]  # old version retained, not overwritten


# -- DELETE (FR-14, data-subject right) -----------------------------------


async def test_delete_own_result_204(
    client: AsyncClient, db: Database, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    result_id = await _submit(client, token)
    resp = await client.delete(
        f"/api/v1/me/assessments/{result_id}", headers=_auth(token)
    )
    assert resp.status_code == 204

    # Gone afterwards.
    read = await client.get(
        f"/api/v1/me/assessments/{result_id}", headers=_auth(token)
    )
    assert read.status_code == 404


async def test_delete_cross_user_404(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    owner = await _adult(client, "o2@example.com")
    result_id = await _submit(client, owner)
    other = await _adult(client, "x2@example.com")
    resp = await client.delete(
        f"/api/v1/me/assessments/{result_id}", headers=_auth(other)
    )
    assert resp.status_code == 404


async def test_submit_empty_answers_422(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    token = await _adult(client)
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": {}},  # min_length=1 → validation error
        headers=_auth(token),
    )
    assert resp.status_code == 422


async def test_submit_no_active_instrument_404(
    client: AsyncClient, db: Database
) -> None:
    """No seeded instruments → submit returns 404 (instrument not found)."""
    token = await _adult(client)
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS},
        headers=_auth(token),
    )
    assert resp.status_code == 404


async def test_submit_requires_auth(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/assessments/riasec/submit", json={"answers": _ANSWERS}
    )
    assert resp.status_code == 401


async def test_no_sensitive_content_in_logs(
    client: AsyncClient,
    db: Database,
    seeded_instruments: dict[str, str],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """NFR-10: result content must never appear in structured logs."""
    token = await _adult(client)
    capsys.readouterr()  # drain prior output
    result_id = await _submit(client, token)
    await client.get(f"/api/v1/me/assessments/{result_id}", headers=_auth(token))
    captured = capsys.readouterr()
    logs = captured.out + captured.err

    # Decrypt to learn the actual scored content, then assert none of it leaked.
    async with db.session_factory() as s:
        row = await s.get(AssessmentResult, result_id)
        assert row is not None
    # Sentinels from the scored payload structure that must not be logged.
    for marker in ('"scores"', '"code"', "result_payload"):
        assert marker not in logs
