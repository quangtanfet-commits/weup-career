# P2 Slice Design Note: Labor Market Intelligence

**Date:** 2026-06-04
**Spec refs:** spec.md §3.4 (FR-34/FR-35), §5 (LaborMarketSnapshot), §6 (API); ADR-015
**Status:** Implementing

---

## 1. Tables Added

### `labor_market_snapshot`

| Column | Type | Constraints | Purpose |
|---|---|---|---|
| `id` | String(36) | PK, UUID | Primary key (UUIDMixin) |
| `sector` | String(128) | NOT NULL, indexed | Occupational sector; join key to CareerProfile by sector |
| `salary_range` | String(128) | NOT NULL | Human-readable salary band (e.g., "15–30 triệu VNĐ/tháng") |
| `demand_forecast` | String(255) | NOT NULL | Demand direction label (e.g., "tăng mạnh", "ổn định") |
| `required_skills` | String(512) | NOT NULL | Comma-joined skill labels (project convention, SQLite-portable) |
| `region` | String(128) | NOT NULL, indexed | Vùng/region (e.g., "toàn quốc", "Hà Nội") |
| `source_ref` | String(255) | **NOT NULL** — schema-level constraint | Provenance guard: citation of authoritative source |
| `as_of_date` | Date | **NOT NULL** — schema-level constraint | Data timestamp; used for staleness detection (NFR-26) |
| `version` | Integer | NOT NULL, default=1 | Version for content governance |
| `created_at` | DateTime(tz) | NOT NULL | Row creation time (TimestampMixin) |

**Staleness threshold:** `as_of_date` older than 365 days is considered stale. API signals "no LMI data" (empty list + `lmi_data_status: "no_data"`) for stale or missing snapshots.

### No new join tables

`CareerProfile` is linked to `LaborMarketSnapshot` by matching `CareerProfile.field` to `LaborMarketSnapshot.sector` at query time (no FK column). This keeps the schema lean and avoids migration coupling to the existing `career_profile` table.

---

## 2. Endpoints Added

### New: `GET /api/v1/labor-market/snapshots`

- Auth: Bearer required (same pattern as careers)
- Query params: `sector` (optional), `region` (optional)
- Returns: empty list when no data — clean, not an error (FR-34)
- Staleness: stale snapshots (as_of_date > 365 days ago) are excluded and signaled via response header / status field

### Modified: `GET /api/v1/careers` (FR-35 extension)

Added optional `sort_by_demand` query param. When `sort_by_demand=true`:
- Careers with a matching non-stale `LaborMarketSnapshot` by sector float to the top
- Each career detail response gains an `lmi_status` field: `"available"`, `"stale"`, or `"no_data"`
- This is additive — the existing filter params are unchanged

### Modified: `GET /api/v1/careers/{id}` (FR-35)

Detail response gains `lmi_status` and `lmi_snapshot` (nullable) fields so the frontend can display "chưa có dữ liệu TTLĐ" when no non-stale snapshot exists.

---

## 3. Provenance Enforcement

Provenance is enforced at **three layers**:

1. **Schema level:** `source_ref` and `as_of_date` are `NOT NULL` in the SQLAlchemy model and the Alembic migration. A DB insert without them raises `IntegrityError`.
2. **Service level:** `LaborMarketService.create_snapshot()` validates that `source_ref` is non-empty and `as_of_date` is not in the future. Raises `ValidationError` (422) on violation.
3. **Seed level:** `app/labor_market/seed.py` creates **zero rows**. The framework is present but no fabricated data is inserted. Real data enters only when an authoritative source (HTTT TTLĐ quốc gia etc.) is available.

---

## 4. Tests Coverage Plan

| Test | Type | What it proves |
|---|---|---|
| `test_list_snapshots_empty` | integration | Empty list returned cleanly when no data |
| `test_list_snapshots_filter_sector` | integration | Sector filter works |
| `test_list_snapshots_filter_region` | integration | Region filter works |
| `test_snapshot_provenance_rejection_no_source_ref` | unit/integration | Missing source_ref → 422 |
| `test_snapshot_provenance_rejection_no_as_of_date` | unit/integration | Missing as_of_date → 422 (caught at schema level too) |
| `test_stale_snapshot_excluded` | integration | Snapshot older than 365d is excluded |
| `test_careers_lmi_status_no_data` | integration | Career with no snapshot → lmi_status="no_data" |
| `test_careers_lmi_status_available` | integration | Career with fresh snapshot → lmi_status="available" |
| `test_careers_sort_by_demand` | integration | sort_by_demand=true floats matched careers to top |
| `test_seed_empty_framework` | unit | Seed creates zero snapshot rows |
| `test_repo_list_no_filter` | unit | Repository list without filters |

---

## 5. Invariants Not Touched

- CP-1..CP-8 are untouched. This module has no consent gate.
- `auth/`, `guardians/`, `assessments/`, `reco/` modules are read-only referenced.
- `CareerProfile.labor_market_outlook` (human-readable prose) is preserved as-is.

---

## 6. Migration

- Revision ID: `e4f5a6b7c8d9`
- `down_revision`: `d3e4f5a6b7c8` (the current head per task spec)
- Two heads expected (parallel stream); lead serializes at integration.
