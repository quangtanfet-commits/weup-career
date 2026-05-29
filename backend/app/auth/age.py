"""Age-band derivation from date of birth (FR-01, spec.md §5).

Bands: under_16 / 16_17 / adult (≥18). The under-16 boundary is the legal
consent gate (legal-basis §6 / NĐ 147/2024) and is configurable via
``consent_age_threshold`` (default 16).
"""

from __future__ import annotations

from datetime import date

from app.core.enums import AgeBand


def calculate_age(dob: date, *, today: date | None = None) -> int:
    ref = today or date.today()
    years = ref.year - dob.year
    if (ref.month, ref.day) < (dob.month, dob.day):
        years -= 1
    return years


def derive_age_band(
    dob: date,
    *,
    today: date | None = None,
    threshold: int = 16,
) -> AgeBand:
    """Map an age to a band. ``threshold`` is the under-X consent boundary."""
    age = calculate_age(dob, today=today)
    if age < threshold:
        return AgeBand.UNDER_16
    if age < 18:
        return AgeBand.BAND_16_17
    return AgeBand.ADULT
