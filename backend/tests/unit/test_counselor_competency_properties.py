"""Property-based fuzz for the counselor-competency codec + version sequencing.

Gate 2 of the FR-103 assurance pass (docs/assurance/counselor-competency-fr103.md).

The scores codec persists ``dict[str, int]`` as a semicolon-joined ``CODE:rating``
string (SQLite-portable). These properties pin its contract:

- round-trip is lossless on the real ``CC-NN`` domain (and for any int rating);
- the encoding is canonical (sorted by code) and order-independent;
- the ``:``/``;`` delimiters define a *lossy boundary* — codes carrying either
  delimiter are dropped/mangled. This is pinned explicitly rather than relied on
  silently: it is the reason the domain is constrained to delimiter-free codes.

Version monotonicity is DB-backed: a fresh in-memory database per example, so
Hypothesis examples never share state.
"""

from __future__ import annotations

import asyncio

from app.core.database import Base
from app.core.models import new_uuid, utcnow
from app.counselor_competency.models import CounselorSelfAssessment
from app.counselor_competency.repository import SqlCounselorCompetencyRepo
from app.counselor_competency.service import _decode_scores, _encode_scores
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# The real framework uses the ``CC-NN`` shape — delimiter- and whitespace-free,
# so it round-trips losslessly. Round-trip properties use this domain.
_cc_codes = st.from_regex(r"CC-[0-9]{2}", fullmatch=True)
# Broader keys for the *ordering* properties (canonical sort, order-independence,
# determinism). These never round-trip, so codes that ``.strip()`` would alter are
# harmless here; the assertions compare against a same-keys reference encoding.
_varied_codes = st.text(
    alphabet=st.characters(blacklist_characters=":;", blacklist_categories=("Cc",)),
    min_size=1,
    max_size=12,
)
_ratings_domain = st.integers(min_value=1, max_value=5)  # the self-assessment range
_ratings_any_int = st.integers(min_value=-10_000, max_value=10_000)


@settings(deadline=None)
@given(st.dictionaries(_cc_codes, _ratings_domain, max_size=6))
def test_codec_round_trip_cc_shape(scores: dict[str, int]) -> None:
    """decode(encode(s)) == s for the real CC-NN domain, ratings 1..5."""
    assert _decode_scores(_encode_scores(scores)) == scores


@settings(deadline=None)
@given(st.dictionaries(_cc_codes, _ratings_any_int, max_size=6))
def test_codec_round_trip_arbitrary_int_ratings(scores: dict[str, int]) -> None:
    """Codec contract is wider than the API domain: any int rating round-trips
    (on the real CC-NN code shape; the rating axis spans far beyond 1..5)."""
    assert _decode_scores(_encode_scores(scores)) == scores


@settings(deadline=None)
@given(st.dictionaries(_varied_codes, _ratings_any_int, max_size=10))
def test_encode_is_canonical_and_order_independent(scores: dict[str, int]) -> None:
    """Encoding is sorted-by-code and independent of dict insertion order."""
    expected = ";".join(f"{k}:{scores[k]}" for k in sorted(scores))
    assert _encode_scores(scores) == expected
    reordered = dict(reversed(list(scores.items())))
    assert _encode_scores(reordered) == _encode_scores(scores)


@settings(deadline=None)
@given(st.dictionaries(_varied_codes, _ratings_any_int, max_size=10))
def test_encode_is_deterministic(scores: dict[str, int]) -> None:
    assert _encode_scores(scores) == _encode_scores(scores)


def test_delimiter_boundary_is_lossy_and_pinned() -> None:
    """Explicit lossy-domain pin: delimiters in a code break the round-trip.

    A code containing ``:`` makes the rating unparseable → the entry is dropped.
    A code containing ``;`` splits into a spurious second entry. This is *why*
    the codec's safe domain is delimiter-free CC-NN codes; pin it so a future
    refactor that "fixes" one case without escaping cannot do so silently.
    """
    # Embedded ':' -> "A:B:3"; rating "B:3" is non-integer -> entry dropped.
    assert _decode_scores(_encode_scores({"A:B": 3})) == {}
    # Embedded ';' -> "A;B:3"; "A" has no colon (dropped), "B:3" -> {"B": 3}.
    assert _decode_scores(_encode_scores({"A;B": 3})) == {"B": 3}


# -- DB-backed version monotonicity ------------------------------------------


async def _versions_for_n_assessments(n: int) -> list[int]:
    """Insert n assessments for one counselor in a fresh DB; return next_version()
    observed before each insert (the assigned version sequence)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        factory = async_sessionmaker(bind=engine, expire_on_commit=False)
        counselor_id = new_uuid()
        assigned: list[int] = []
        async with factory() as session:
            repo = SqlCounselorCompetencyRepo(session)
            for _ in range(n):
                version = await repo.next_version(counselor_id=counselor_id)
                assigned.append(version)
                await repo.add_self_assessment(
                    CounselorSelfAssessment(
                        id=new_uuid(),
                        counselor_id=counselor_id,
                        version=version,
                        scores="",
                        suggested_development_path="",
                        created_at=utcnow(),
                    )
                )
        return assigned
    finally:
        await engine.dispose()


@settings(deadline=None)
@given(st.integers(min_value=1, max_value=12))
def test_version_sequence_is_1_to_n(n: int) -> None:
    """Successive assessments for one counselor get versions exactly 1..N."""
    assigned = asyncio.run(_versions_for_n_assessments(n))
    assert assigned == list(range(1, n + 1))
