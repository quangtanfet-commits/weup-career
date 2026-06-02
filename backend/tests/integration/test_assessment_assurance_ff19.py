"""FF-19 assurance-gating integration tests (guardian-verification.md §9).

Proves the gate is wired AND configurable:
  - default SENSITIVE_MIN_ASSURANCE=low → email-consent (LOW) link unlocks
    under-16 sensitive submit (MVP interim; no hard block).
  - SENSITIVE_MIN_ASSURANCE=medium → the same LOW link is blocked with
    403 ASSURANCE_LEVEL_TOO_LOW (the post-VNeID policy).
Adults are never assurance-gated.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from app.api.deps import mailer as mailer_dep
from app.core.config import Settings
from app.core.database import Database
from app.core.mailer import CapturingMailer
from app.main import create_app
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from tests.conftest import (
    child_dob,
    mailer_of,
    make_settings,
    register_and_verify,
)

pytestmark = pytest.mark.asyncio

_ANSWERS = {"R_1": 5, "R_2": 4, "I_1": 3}


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def medium_settings() -> Settings:
    return make_settings(sensitive_min_assurance="medium")


async def _make_child_with_low_consent(client: AsyncClient) -> str:
    mailer = mailer_of(client)
    child_token = (
        await register_and_verify(
            client,
            mailer,
            email="child@example.com",
            dob=child_dob(12),
            school_level="lower_secondary",
        )
    )["access_token"]
    guardian_token = (
        await register_and_verify(client, mailer, email="parent@example.com", dob="1980-01-01")
    )["access_token"]
    invite = await client.post(
        "/api/v1/guardians/invite",
        json={"guardian_email": "parent@example.com", "relationship": "mother"},
        headers=_auth(child_token),
    )
    # Email-method link → assurance LOW (slice-1 default).
    await client.post(
        "/api/v1/guardians/consent",
        json={"guardian_link_id": invite.json()["id"]},
        headers=_auth(guardian_token),
    )
    # Re-login so the JWT reflects the now-active account.
    return (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "child@example.com", "password": "Password123"},
        )
    ).json()["access_token"]


@pytest_asyncio.fixture
async def medium_client(
    medium_settings: Settings, db: Database, seeded_instruments: dict[str, str]
) -> AsyncGenerator[AsyncClient, None]:
    app = create_app(medium_settings)
    app.state.db = db
    # N-3: capture verification mail so register_and_verify can replay the token
    # (mirrors the shared ``client`` fixture wiring in conftest).
    mailer = CapturingMailer()
    app.state.captured_mailer = mailer
    app.dependency_overrides[mailer_dep] = lambda: mailer
    transport = ASGITransport(app=app)
    async with LifespanManager(app):
        app.state.db = db
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


async def test_low_assurance_blocked_at_medium_minimum(
    medium_client: AsyncClient,
) -> None:
    child_token = await _make_child_with_low_consent(medium_client)
    resp = await medium_client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS},
        headers=_auth(child_token),
    )
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "ASSURANCE_LEVEL_TOO_LOW"


async def test_adult_not_assurance_gated_at_medium_minimum(
    medium_client: AsyncClient,
) -> None:
    token = (
        await register_and_verify(
            medium_client, mailer_of(medium_client), email="adult@example.com", dob="1990-01-01"
        )
    )["access_token"]
    resp = await medium_client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS},
        headers=_auth(token),
    )
    assert resp.status_code == 201


async def test_low_assurance_allowed_at_default_low_minimum(
    client: AsyncClient, seeded_instruments: dict[str, str]
) -> None:
    """MVP default (low): the LOW email-consent link unlocks submit (no block)."""
    child_token = await _make_child_with_low_consent(client)
    resp = await client.post(
        "/api/v1/assessments/riasec/submit",
        json={"answers": _ANSWERS},
        headers=_auth(child_token),
    )
    assert resp.status_code == 201
