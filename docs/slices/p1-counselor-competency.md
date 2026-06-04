# Slice Design Note: P1 — Counselor Competency Framework & Self-Assessment

**Date:** 2026-06-04
**Spec refs:** §3.11 FR-100..103, §5 (data model), §6 (API)
**ADR:** ADR-016-counselor-competency-framework.md
**Status:** Implementation

---

## Scope

New, independent module `app/counselor_competency/` — fully separate from the
learner 12-competency tree (`app/competency/`). Does NOT import or reuse any
entity from that tree.

## Entities

### `CounselorCompetency` (table `counselor_competency`)

Framework entry for a counseling-practice competency.

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `code` | String(16) UNIQUE | e.g. `CC-01` |
| `name_vi` | String(255) | Vietnamese name |
| `name_en` | String(255) | English name |
| `description` | Text | Detailed description |
| `source_ref` | String(255) | Legal/normative source (TT 18/2025) |

### `CounselorSelfAssessment` (table `counselor_self_assessment`)

A counselor's versioned self-assessment snapshot.

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) PK | UUID |
| `counselor_id` | String(36) FK→`user.id` | Owning counselor |
| `version` | Integer | Monotonic per-counselor version |
| `scores` | Text | Semicolon-encoded `CODE:rating` pairs (e.g. `CC-01:4;CC-02:3`) |
| `suggested_development_path` | Text | Textual suggestion + explanation |
| `created_at` | DateTime(tz) | Submission timestamp |

**scores encoding:** `CODE:rating` pairs joined by `;` (no Postgres ARRAY/JSON).
Schema layer splits → dict. Mirrors project convention (comma/semicolon-encoded strings for SQLite portability).

## Authorization

- **Counselor membership** is derived from `SchoolMembership.role == COUNSELOR`.
- A `require_counselor` dependency checks this per-request against the DB
  (never from the JWT alone), following the same pattern as the school channel.
- Counselor self-assessments belong to the calling counselor only — no
  cross-counselor read is exposed at MVP.

## CP-1 separation (FR-103, ADR-016 §3)

Counselor self-assessment data is the **counselor's own personal data**. It:
- Does NOT enter the guardian-consent gate (that gate covers under-16 student
  career data only, per CP-1 / `require_career_data_consent`).
- Does NOT touch student career data, assessments, recommendations, or any
  learner entity.
- Does NOT go through CP-5/CP-6 (learner recommendation rationale/human-in-the-loop).

A negative regression test (`test_cp1_separation_counselor_no_guardian_needed`)
asserts that a counselor with NO guardian link can create and read their own
self-assessment without a 403.

## CP-4 unaffected

The new endpoints do NOT widen counselor authority over students. A test
(`test_cp4_new_endpoints_do_not_widen_authority`) confirms that a counselor
holding a counselor membership still cannot access another counselor's or a
student's self-assessment through the new routes.

## Development-path suggestion (FR-102)

`CounselorCompetencyService.suggest_development_path()` runs in its own flow:

1. Parse `scores` to identify competencies rated below a threshold (≤2 on a 1–5 scale).
2. For each low-rated competency, append a recommendation to attend training aligned with
   its `source_ref` (TT 18/2025).
3. Return `(path_text, explanation_text)` — both are plain text, stored together
   as `suggested_development_path`.

This does NOT import from `app/reco/` or `app/competency/`.

## API endpoints

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/v1/counselor/competencies` | Bearer + counselor membership | List the framework |
| `POST` | `/api/v1/me/counselor/self-assessments` | Bearer + counselor membership | Create self-assessment |
| `GET` | `/api/v1/me/counselor/self-assessments` | Bearer + counselor membership | Own assessment history |

## Alembic migration

Revision: `e5f6a7b8c9d0`
Down-revision: `d3e4f5a6b7c8` (branch off n03 head — two heads expected;
serialized at integration, per task instructions).

## Seed

`app/counselor_competency/seed.py` seeds 6 framework competency codes
(CC-01..CC-06) grounded in TT 18/2025 (tư vấn tâm lý/hướng nghiệp học đường).
