"""Assurance gating for sensitive data of under-16 users (FF-19).

guardian-verification.md §2 + §9 define a policy: sensitive data (RIASEC / [CRED_D17EA8A0]
MBTI results) of an under-16 child should only be processed when the guardian
link's ``assurance_level`` meets a configured minimum.

This is **wired but configurable** (``SENSITIVE_MIN_ASSURANCE``). The MVP default
is ``LOW`` because VNeID is not integrated yet, so an email-consent (LOW) link
must still unlock processing — otherwise no under-16 could use the platform,
contradicting the slice-1 consent flow. The gate is therefore a no-op at the
default and becomes a hard requirement once the operator flips the default to
``MEDIUM`` post-VNeID. Over-16 users are never assurance-gated.
"""

from __future__ import annotations

from app.core.enums import AssuranceLevel
from app.core.exceptions import AssuranceTooLowError

# Total order over assurance levels (low < medium < high).
_ORDER: dict[AssuranceLevel, int] = {
    AssuranceLevel.LOW: 0,
    AssuranceLevel.MEDIUM: 1,
    AssuranceLevel.HIGH: 2,
}


def meets_minimum(level: AssuranceLevel, minimum: AssuranceLevel) -> bool:
    """Return True iff ``level`` is at least ``minimum`` in the assurance order."""
    return _ORDER[level] >= _ORDER[minimum]


def require_assurance(level: AssuranceLevel | None, minimum: AssuranceLevel) -> None:
    """Raise :class:`AssuranceTooLowError` when ``level`` is below ``minimum``.

    ``level`` is ``None`` only when no verified guardian link exists; that is
    treated as failing any minimum above LOW.
    """
    effective = level if level is not None else AssuranceLevel.LOW
    if not meets_minimum(effective, minimum):
        raise AssuranceTooLowError(details={"required": minimum.value, "actual": effective.value})
