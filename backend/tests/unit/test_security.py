"""Password hashing + JWT unit/property tests (FR-06, ADR-008, CP-7 token bits)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from app.core.exceptions import TokenError
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from hypothesis import given
from hypothesis import settings as hyp_settings
from hypothesis import strategies as st

from tests.conftest import make_settings


def test_password_roundtrip() -> None:
    h = hash_password("Password123", rounds=4)
    assert h != "Password123"
    assert verify_password("Password123", h)
    assert not verify_password("WrongPass1", h)


def test_verify_with_malformed_hash_is_false() -> None:
    assert not verify_password("Password123", "not-a-bcrypt-hash")


def test_long_password_not_truncated() -> None:
    # bcrypt's 72-byte limit is bypassed by SHA-256 pre-hash.
    long_a = "A" * 100 + "1a"
    long_b = "A" * 100 + "1b"
    h = hash_password(long_a, rounds=4)
    assert verify_password(long_a, h)
    assert not verify_password(long_b, h)


@given(st.text(min_size=1, max_size=200))
@hyp_settings(max_examples=50, deadline=None)
def test_hash_verify_property(pw: str) -> None:
    h = hash_password(pw, rounds=4)
    assert verify_password(pw, h)


def test_refresh_token_hash_stable_and_unique() -> None:
    t1 = generate_refresh_token()
    t2 = generate_refresh_token()
    assert t1 != t2
    assert hash_refresh_token(t1) == hash_refresh_token(t1)
    assert hash_refresh_token(t1) != hash_refresh_token(t2)
    assert len(hash_refresh_token(t1)) == 64  # sha256 hex


def _token(**kw: object) -> str:
    s = make_settings()
    base = {
        "settings": s,
        "subject": "usr_1",
        "email": "a@b.com",
        "user_type": "student",
        "age_band": "under_16",
        "account_status": "active",
        "roles": ["student"],
    }
    base.update(kw)
    return create_access_token(**base)  # type: ignore[arg-type]


def test_access_token_roundtrip_claims() -> None:
    s = make_settings()
    token = _token()
    claims = decode_access_token(token, settings=s)
    assert claims["sub"] == "usr_1"
    assert claims["age_band"] == "under_16"
    assert claims["iss"] == "weup-api"
    assert "jti" in claims


def test_expired_token_rejected() -> None:
    s = make_settings()
    past = datetime.now(UTC) - timedelta(hours=1)
    token = _token(now=past)
    with pytest.raises(TokenError):
        decode_access_token(token, settings=s)


def test_tampered_signature_rejected() -> None:
    s = make_settings()
    token = _token()
    with pytest.raises(TokenError):
        decode_access_token(token + "x", settings=s)


def test_wrong_issuer_rejected() -> None:
    issuing = make_settings(jwt_issuer="other-iss")
    verifying = make_settings()  # issuer weup-api
    token = _token(settings=issuing)
    with pytest.raises(TokenError):
        decode_access_token(token, settings=verifying)


def test_wrong_secret_rejected() -> None:
    token = _token()
    other = make_settings(secret_key="z" * 40)
    with pytest.raises(TokenError):
        decode_access_token(token, settings=other)
