# Security & Quality triage — 2026-06

**Status:** Design + actioned
**Date:** 2026-06-02
**Owner:** Platform / Security
**Scope:** Triage and remediation of every open item on the GitHub **Security** tab
("Security and quality"): code scanning (CodeQL) + Dependabot. Secret scanning: 0 open.
**Related:** [ADR-008 Security Controls](../adr/ADR-008-security-controls.md),
[dependabot-2026-06.md](./dependabot-2026-06.md),
[security-scan-fix-2026-06.md](./security-scan-fix-2026-06.md)

---

## 1. Inventory (at triage time)

| Source | # | Severity | Finding | Location |
|---|---|---|---|---|
| CodeQL | 1 | high | `py/weak-sensitive-data-hashing` | `backend/app/core/security.py:29` |
| CodeQL | 2 | high | `py/weak-sensitive-data-hashing` | `backend/app/core/security.py:36` |
| CodeQL | 3 | high | `js/insecure-randomness` | `frontend/tests/e2e/fixtures/auth.ts:30` |
| Dependabot | 4 | medium | `postcss < 8.5.10` (CVE-2026-41305, GHSA-qx2v-qp2m-jg93) | `frontend/package-lock.json` |
| Dependabot | 3 | medium | `pytest < 9.0.3` (CVE-2025-71176, GHSA-6w46-j5rx-g56g) | `backend/uv.lock` |

---

## 2. CodeQL #1 / #2 — `py/weak-sensitive-data-hashing` → **false positive (dismiss)**

`hash_password` / `verify_password` SHA-256-prehash the password, then **bcrypt**-hash
the digest (cost 12, per-call salt):

```python
prehashed = hashlib.sha256(password.encode("utf-8")).digest()
return bcrypt.hashpw(prehashed, bcrypt.gensalt(rounds=12)).decode("ascii")
```

- The **real** password hash is bcrypt — slow, salted, cost ≥12 (FR-06, ADR-008). The
  SHA-256 step only sidesteps bcrypt's 72-byte input truncation, the standard Passlib
  `bcrypt_sha256` idiom. CodeQL's taint analysis misreads the intermediate SHA-256 as
  the final at-rest hash of sensitive data.
- The one genuine risk of binary-digest prehashing — bcrypt truncating the digest at an
  embedded `0x00` byte — was **empirically ruled out** on the pinned `bcrypt 4.3.0`: a
  forged input sharing the pre-null prefix of a real digest fails `checkpw`, i.e. bcrypt
  consumes the full 32-byte digest, no null truncation.

**Action:** dismiss both as `false positive`. Changing the algorithm would invalidate
every stored hash (forced migration) for zero security gain — that would be the actual
regression. Dismissal rationale recorded here and in the alert comment.

## 3. CodeQL #3 — `js/insecure-randomness` → **fix at source**

`uniqueEmail()` (e2e fixture) used `Math.random()` to make test emails unique. Not
security-sensitive (no secret/token derived from it), but rather than dismiss, the call
is replaced with `node:crypto` `randomUUID()` so the alert is removed at source and the
fixture is robust against collisions under parallel runs.

## 4. Dependabot #4 — `postcss < 8.5.10` → **real, bump**

CVE-2026-41305: XSS via unescaped `</style>` in PostCSS's CSS stringifier. The
top-level dev dependency already resolves to a patched 8.5.x, but `next@16.2.6` bundles
`postcss@8.4.31` (< 8.5.10) transitively — that nested copy is what Dependabot flags.
Fixed by an `overrides` pin forcing `postcss` ≥ 8.5.10 across the tree (same major,
backward compatible) and refreshing `package-lock.json`.

## 5. Dependabot #3 — `pytest < 9.0.3` → **real, coordinated bump**

CVE-2025-71176: insecure `tmpdir` handling. Dev/test-only. First patched: 9.0.3.
`pytest` was pinned `>=8.3,<9`, and `pytest-asyncio` `>=0.24,<0.25` does not support
pytest 9 — so this is a **coordinated** bump (pytest + pytest-asyncio), validated by a
full backend suite re-run. Exact resolved versions recorded in §7 after the run.

---

## 6. Remediation summary

| # | Action | Reversible? |
|---|---|---|
| 1,2 | Dismiss as `false positive` (API + comment) | Yes (re-open) |
| 3 | Code fix: `crypto.randomUUID()` in fixture | n/a |
| 4 | `overrides: postcss ^8.5.10` + lockfile refresh | Yes |
| 3 (dep) | `pytest>=9.0.3` + compatible `pytest-asyncio`; full suite | Yes |

## 7. Verification gates

- `npm ls postcss` shows no instance `< 8.5.10`; frontend build + lint clean.
- Backend suite green on bumped pytest; coverage gate unchanged (≥90% meaningful).
- CodeQL #1/#2 show `dismissed (false positive)`; #3 absent on next scan.
- Dependabot #3/#4 auto-close as `fixed` after merge.

## 8. Out of scope / follow-up

- python-jose → PyJWT migration (tracked in [dependabot-2026-06.md](./dependabot-2026-06.md) §5).
- Full-workflow third-party action SHA pinning.
