"""Field crypto unit + property tests (ADR-011)."""

from __future__ import annotations

import base64

import pytest
from app.core.crypto import FieldCrypto, FieldCryptoError
from hypothesis import given
from hypothesis import strategies as st

KEY = "a" * 32
KEY2 = "b" * 32


def test_roundtrip_basic() -> None:
    fc = FieldCrypto(KEY)
    token = fc.encrypt("hello sensitive")
    assert token.startswith("v1:")
    assert fc.decrypt(token) == "hello sensitive"


def test_ciphertext_is_not_plaintext() -> None:
    fc = FieldCrypto(KEY)
    token = fc.encrypt("RIASEC=R")
    assert "RIASEC" not in token


def test_nonce_makes_ciphertext_nondeterministic() -> None:
    fc = FieldCrypto(KEY)
    assert fc.encrypt("same") != fc.encrypt("same")


def test_wrong_key_fails_authentication() -> None:
    token = FieldCrypto(KEY).encrypt("secret")
    with pytest.raises(FieldCryptoError, match="authentication failed"):
        FieldCrypto(KEY2).decrypt(token)


def test_empty_key_rejected() -> None:
    with pytest.raises(FieldCryptoError):
        FieldCrypto("")


def test_key_version_exposed() -> None:
    assert FieldCrypto(KEY, version=3).key_version == 3
    token = FieldCrypto(KEY, version=3).encrypt("x")
    assert token.startswith("v3:")


@pytest.mark.parametrize(
    "bad",
    [
        "",  # empty
        "no-separator",  # missing ':'
        "x1:" + base64.b64encode(b"short").decode(),  # bad version prefix
        "v1:not-base64!!!",  # invalid base64
        "v1:" + base64.b64encode(b"tiny").decode(),  # too short (<= nonce)
    ],
)
def test_malformed_ciphertext_rejected(bad: str) -> None:
    with pytest.raises(FieldCryptoError):
        FieldCrypto(KEY).decrypt(bad)


def test_tampered_ciphertext_rejected() -> None:
    fc = FieldCrypto(KEY)
    token = fc.encrypt("payload")
    version, _, blob = token.partition(":")
    raw = bytearray(base64.b64decode(blob))
    raw[-1] ^= 0x01  # flip a tag bit
    tampered = f"{version}:{base64.b64encode(bytes(raw)).decode()}"
    with pytest.raises(FieldCryptoError):
        fc.decrypt(tampered)


@given(st.text(max_size=2000))
def test_roundtrip_property(plaintext: str) -> None:
    fc = FieldCrypto(KEY)
    assert fc.decrypt(fc.encrypt(plaintext)) == plaintext
