"""Field-level encryption for sensitive data (ADR-011, CP-3 support).

Sensitive fields (e.g. `AssessmentResult.result_payload`) are encrypted at the
application layer with `FIELD_ENCRYPTION_KEY` — separate from `SECRET_KEY`.

A `key_version` prefix is stored with every ciphertext so keys can be rotated
and historical data re-encrypted (ADR-011 "Consequences"). No sensitive data
exists in the slice-1 schema yet, but the primitive is provided and fully
tested so downstream slices wire it in without re-deriving the format.

Wire format (string):  ``v<version>:<base64(nonce||ciphertext||tag)>``
Algorithm: AES-256-GCM (authenticated encryption).
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_NONCE_BYTES = 12
_CURRENT_VERSION = 1
_SEPARATOR = ":"


class FieldCryptoError(ValueError):
    """Raised when ciphertext is malformed or fails authentication."""


def _derive_key(secret: str) -> bytes:
    """Derive a stable 256-bit AES key from the configured secret.

    The secret is operator-supplied high-entropy material (``openssl rand
    -hex 32``); SHA-256 normalises arbitrary-length input to exactly 32 bytes.
    """
    return hashlib.sha256(secret.encode("utf-8")).digest()


class FieldCrypto:
    """Encrypt/decrypt sensitive string fields with versioned AES-256-GCM."""

    def __init__(self, key: str, *, version: int = _CURRENT_VERSION) -> None:
        if not key:
            raise FieldCryptoError("encryption key must not be empty")
        self._version = version
        self._aesgcm = AESGCM(_derive_key(key))

    def encrypt(self, plaintext: str) -> str:
        """Encrypt UTF-8 ``plaintext`` to the versioned wire format."""
        import os

        nonce = os.urandom(_NONCE_BYTES)
        ciphertext = self._aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
        blob = base64.b64encode(nonce + ciphertext).decode("ascii")
        return f"v{self._version}{_SEPARATOR}{blob}"

    def decrypt(self, token: str) -> str:
        """Decrypt a value produced by :meth:`encrypt`.

        Raises :class:`FieldCryptoError` on any malformation or auth failure
        (fail-closed: never returns partial/forged plaintext).
        """
        if not token or _SEPARATOR not in token:
            raise FieldCryptoError("malformed ciphertext: missing version prefix")
        version_part, _, blob = token.partition(_SEPARATOR)
        if not version_part.startswith("v"):
            raise FieldCryptoError("malformed ciphertext: bad version prefix")
        try:
            raw = base64.b64decode(blob, validate=True)
        except (ValueError, base64.binascii.Error) as exc:  # type: ignore[attr-defined]
            raise FieldCryptoError("malformed ciphertext: invalid base64") from exc
        if len(raw) <= _NONCE_BYTES:
            raise FieldCryptoError("malformed ciphertext: too short")
        nonce, ciphertext = raw[:_NONCE_BYTES], raw[_NONCE_BYTES:]
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, None)
        except InvalidTag as exc:
            raise FieldCryptoError("authentication failed: ciphertext tampered") from exc
        return plaintext.decode("utf-8")

    @property
    def key_version(self) -> int:
        return self._version
