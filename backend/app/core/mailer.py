"""Outbound email port + adapters (N-3, PT-04 residual).

No real SMTP transport ships in the MVP — there is no mail infrastructure and
the devcontainer cannot run one. Email is therefore modeled as a hexagonal port
so the verification flow is fully exercised in dev/test through swappable
adapters, and a real transport can be dropped in later without touching the
service layer (ADR-009 ports-and-adapters).

Adapters:
- ``ConsoleMailer`` (development): logs the verification link to stdout.
- ``CapturingMailer`` (test): records sent mail in-memory so a test can pull the
  token out of the link and POST it back.
- ``SmtpMailer`` (production seam): fail-fast placeholder — wiring a real SMTP
  transport is explicitly out of MVP scope (email-verification §8).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import structlog

_log = structlog.get_logger(__name__)


@dataclass(frozen=True)
class SentEmail:
    """A delivered verification email (recorded by the test adapter)."""

    to: str
    verify_url: str


@runtime_checkable
class IMailer(Protocol):
    """Port: deliver an email-verification link to an address.

    Callers treat delivery as best-effort and enumeration-safe: an adapter must
    not raise in a way that lets a caller distinguish a real recipient from a
    synthetic one (the service swallows mailer failures on the resend path).
    """

    async def send_verification_email(self, *, to: str, verify_url: str) -> None: ...


class ConsoleMailer:
    """Dev adapter — logs the verification link (NDJSON) instead of sending.

    Intentionally emits ``verify_url`` (which carries the token) so a developer
    can complete the flow locally. Never selected in production: a real send
    would leak the token to logs otherwise.
    """

    async def send_verification_email(self, *, to: str, verify_url: str) -> None:
        _log.info("mailer.console.verification_email", to=to, verify_url=verify_url)


class CapturingMailer:
    """Test adapter — records sent emails in-memory for assertion/token extraction."""

    def __init__(self) -> None:
        self.sent: list[SentEmail] = []

    async def send_verification_email(self, *, to: str, verify_url: str) -> None:
        self.sent.append(SentEmail(to=to, verify_url=verify_url))

    def last_for(self, to: str) -> SentEmail | None:
        """Most recent email sent to ``to``, or None — what a test asserts on."""
        for email in reversed(self.sent):
            if email.to == to:
                return email
        return None


class SmtpMailer:
    """Production seam — not implemented in the MVP (email-verification §8).

    Fail-fast so a misconfigured production deploy surfaces immediately rather
    than silently dropping verification mail.
    """

    async def send_verification_email(self, *, to: str, verify_url: str) -> None:
        raise NotImplementedError(
            "Real SMTP transport is not configured (out of MVP scope, N-3 §8)."
        )
