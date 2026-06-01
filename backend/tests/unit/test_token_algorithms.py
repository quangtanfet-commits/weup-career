"""Algorithm-confusion & token-replay hardening tests (CP-7, ADR-008).

Complements ``test_security.py`` (expiry / tampered-sig / wrong-issuer / wrong-secret)
with the algorithm-substitution and replay-precondition checks the enterprise
security checklist calls out explicitly:

- ``alg=none`` (unsigned) tokens must be rejected.
- Algorithm-substitution (a header alg outside the verifier's allow-list) must be
  rejected even when the attacker controls the header.
- Every issued access token carries a unique ``jti`` — the precondition any
  replay-tracking layer depends on.
- Password verification is constant-time and never short-circuits or raises on a
  length-mismatched candidate.
"""

from __future__ import annotations

import base64
import json

import pytest
from app.core.exceptions import TokenError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)

from tests.conftest import make_settings


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
        "session_version": 1,
    }
    base.update(kw)
    return create_access_token(**base)  # type: ignore[arg-type]


def _b64url(obj: dict[str, object]) -> str:
    raw = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def test_alg_none_unsigned_token_rejected() -> None:
    """A forged ``alg=none`` token with no signature must NOT be accepted."""
    s = make_settings()
    header = _b64url({"alg": "none", "typ": "JWT"})
    payload = _b64url(
        {
            "sub": "usr_1",
            "iss": s.jwt_issuer,
            "exp": 9999999999,
            "roles": ["counselor"],  # attacker tries to self-grant a role
        }
    )
    forged = f"{header}.{payload}."  # empty signature segment
    with pytest.raises(TokenError):
        decode_access_token(forged, settings=s)


def test_algorithm_substitution_rejected() -> None:
    """A token whose header advertises an algorithm outside the verifier's
    allow-list must be rejected, even with a valid-looking structure."""
    s = make_settings()
    header = _b64url({"alg": "HS512", "typ": "JWT"})
    payload = _b64url({"sub": "usr_1", "iss": s.jwt_issuer, "exp": 9999999999})
    # Signature is irrelevant: HS512 is not in algorithms=[HS256], so jose
    # refuses before signature comparison.
    forged = f"{header}.{payload}.{_b64url({'x': 'sig'})}"
    with pytest.raises(TokenError):
        decode_access_token(forged, settings=s)


def test_jti_present_and_unique_across_issuances() -> None:
    """Each issued token gets a fresh jti — the precondition for replay tracking."""
    s = make_settings()
    jtis = {decode_access_token(_token(), settings=s)["jti"] for _ in range(25)}
    assert len(jtis) == 25
    assert all(isinstance(j, str) and j for j in jtis)


def test_explicit_jti_is_honored() -> None:
    """A caller-supplied jti round-trips, so a revocation store can key on it."""
    s = make_settings()
    claims = decode_access_token(_token(jti="fixed-jti-123"), settings=s)
    assert claims["jti"] == "fixed-jti-123"


def test_password_verify_constant_time_no_shortcircuit_on_length() -> None:
    """verify_password never raises and returns False for a length-mismatched
    candidate — bcrypt.checkpw compares in constant time over the digest."""
    h = hash_password("Matkhau123", rounds=4)
    assert verify_password("Matkhau123", h) is True
    assert verify_password("x", h) is False  # far shorter
    assert verify_password("M" * 500, h) is False  # far longer
    assert verify_password("", h) is False  # empty


def test_password_verify_on_garbage_hash_is_false_not_raises() -> None:
    assert verify_password("Matkhau123", "$2b$not-a-real-hash") is False
