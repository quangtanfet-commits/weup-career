# Assurance note — counselor-competency personal-data path (FR-103)

> Scope: `backend/app/counselor_competency/` on branch `integration/p1-p2`.
> Driver: `/assure` (measurable assurance) for the P1 personal-data path.
> FR-103 — a counselor self-assessment is the counselor's own personal data,
> **outside** the CP-1 guardian-consent gate, and must not leak across
> counselors (CP-4 ownership). This note is doc-first per project rule; it
> records the plan, the one real defect found, and the gate thresholds.

## Why this module is "critical personal data"

- Stores a counselor's self-rating history (`counselor_self_assessment`).
- It is **not** KPI data: `school_admin` cannot read it; only the owning
  counselor can (CP-4 ownership re-derived from `SchoolMembership` per request).
- It deliberately never touches student career data / guardians / consent
  (CP-1 isolation, ADR-016).

Thresholds applied (critical personal-data class): **line ≥ 95%, branch ≥ 90%,
function = 100%.**

## Baseline measured (pre-assure)

| Gate | State |
|---|---|
| Coverage | 99% line, 17/18 branch. Only miss: `seed.py:116-117` — the **idempotent re-seed branch** (not the CLI block, which is already `# pragma: no cover`). |
| mypy `--strict` | **1 error**: `schemas.py:66` unused `type: ignore[arg-type]`. The exact CI command (`mypy app/ --strict --ignore-missing-imports`) reports it, so this local integration branch is currently red on the mypy gate. CI never ran on the merged branch; the B PR passed when the toolchain still needed that ignore. |
| Property fuzz | None on this module (example-based codec/suggest tests only). |
| Evidence bundle | None. |

## Gate 0 — the one real defect (fixed)

`SelfAssessmentResult.created_at` is typed `object` (service.py), but Pydantic's
`BaseModel.__init__` accepts `Any` under mypy-without-plugin, so the
`# type: ignore[arg-type]` on `schemas.py:66` is now dead. Removing it is safe
(no behavior change) and turns the mypy gate green. This is exactly the latent
"unused-ignore" the assure typing gate exists to catch.

## Gates 1–4 (plan)

1. **Coverage → 100%**: add a seeder-idempotency test (run twice → second pass
   takes the `existing is not None` branch, returns identical ids, zero
   duplicate rows). Closes `seed.py:116-117`.
2. **Property fuzz** (Hypothesis): codec round-trip on the real `CC-NN` code
   shape; determinism + canonical sorted form; the delimiter (`:`/`;`) boundary
   pinned as an explicit lossy-domain invariant rather than silently relied on;
   version monotonicity `1..N` (DB-backed). Shrunk failures captured as seeds.
3. **Typing evidence**: `mypy app/counselor_competency/ --strict` = 0 errors
   after Gate 0; no new ignores introduced.
4. **Evidence bundle**: `.assurance/<run-id>/assurance-report.json` + raw
   `coverage.xml`, mypy output, hypothesis seeds/iterations. Reproducible from
   `commit_sha` + thresholds + seeds.

## Explicitly out of scope (separate approval)

- No `.github/workflows/ci.yml` wiring or branch-protection change in this pass.
  The CI hunk that would bind these gates is handed over as a diff for a later,
  separate decision.
- No destructive change. Nothing committed without explicit instruction.
