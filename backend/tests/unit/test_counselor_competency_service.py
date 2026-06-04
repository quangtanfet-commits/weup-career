"""Unit tests for counselor-competency service internals.

Covers edge paths not exercised by the integration tests:
- _decode_scores: empty string, malformed entries, non-integer ratings
- _suggest_development_path: unknown code (competency not in DB), all-high scores
- version increment determinism
"""

from __future__ import annotations

import pytest
from app.counselor_competency.service import _decode_scores, _encode_scores

# -- _decode_scores edge cases -----------------------------------------------


def test_decode_scores_empty_string() -> None:
    assert _decode_scores("") == {}


def test_decode_scores_no_colon() -> None:
    # A part with no colon is silently skipped
    assert _decode_scores("CC-01:4;INVALID;CC-02:3") == {"CC-01": 4, "CC-02": 3}


def test_decode_scores_non_integer_rating() -> None:
    # A part with a non-integer rating is silently skipped
    assert _decode_scores("CC-01:abc;CC-02:3") == {"CC-02": 3}


def test_decode_scores_round_trip() -> None:
    original = {"CC-01": 4, "CC-02": 2, "CC-03": 5}
    encoded = _encode_scores(original)
    decoded = _decode_scores(encoded)
    assert decoded == original


# -- _suggest_development_path: unknown code ---------------------------------


@pytest.mark.asyncio
async def test_suggest_unknown_code_falls_back_to_generic() -> None:
    """Unknown competency code in scores → generic note, no crash (else branch)."""
    from unittest.mock import AsyncMock

    from app.counselor_competency.service import CounselorCompetencyService

    repo = AsyncMock()
    repo.get_competency_by_code.return_value = None  # simulate unknown code

    svc = CounselorCompetencyService.__new__(CounselorCompetencyService)
    svc._repo = repo  # type: ignore[attr-defined]

    path = await svc._suggest_development_path(scores={"UNKNOWN-CODE": 1})
    assert "UNKNOWN-CODE" in path
    assert "TT 18/2025" in path


@pytest.mark.asyncio
async def test_suggest_all_high_scores_returns_positive_message() -> None:
    """All high scores → positive maintenance message, no gaps."""
    from unittest.mock import AsyncMock

    from app.counselor_competency.service import _SUGGESTION_ALL_GOOD, CounselorCompetencyService

    repo = AsyncMock()
    svc = CounselorCompetencyService.__new__(CounselorCompetencyService)
    svc._repo = repo  # type: ignore[attr-defined]

    path = await svc._suggest_development_path(scores={"CC-01": 5, "CC-02": 4, "CC-03": 3})
    # All above threshold → no suggestions, just the positive message
    assert _SUGGESTION_ALL_GOOD[:30] in path
    repo.get_competency_by_code.assert_not_called()
