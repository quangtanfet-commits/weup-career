"""Unit tests for the FF-19 assurance gate (core/assurance.py)."""

from __future__ import annotations

import pytest
from app.core.assurance import meets_minimum, require_assurance
from app.core.enums import AssuranceLevel
from app.core.exceptions import AssuranceTooLowError


def test_meets_minimum_total_order() -> None:
    assert meets_minimum(AssuranceLevel.LOW, AssuranceLevel.LOW)
    assert meets_minimum(AssuranceLevel.MEDIUM, AssuranceLevel.LOW)
    assert meets_minimum(AssuranceLevel.HIGH, AssuranceLevel.MEDIUM)
    assert not meets_minimum(AssuranceLevel.LOW, AssuranceLevel.MEDIUM)
    assert not meets_minimum(AssuranceLevel.MEDIUM, AssuranceLevel.HIGH)


def test_require_assurance_passes_at_or_above_minimum() -> None:
    require_assurance(AssuranceLevel.LOW, AssuranceLevel.LOW)
    require_assurance(AssuranceLevel.HIGH, AssuranceLevel.MEDIUM)


def test_require_assurance_default_low_is_noop() -> None:
    # MVP default: LOW link unlocks under the LOW minimum (interim policy).
    require_assurance(AssuranceLevel.LOW, AssuranceLevel.LOW)


def test_require_assurance_raises_below_minimum() -> None:
    with pytest.raises(AssuranceTooLowError) as exc:
        require_assurance(AssuranceLevel.LOW, AssuranceLevel.MEDIUM)
    assert exc.value.details == {"required": "medium", "actual": "low"}


def test_require_assurance_none_treated_as_low() -> None:
    require_assurance(None, AssuranceLevel.LOW)  # passes at low minimum
    with pytest.raises(AssuranceTooLowError):
        require_assurance(None, AssuranceLevel.MEDIUM)
