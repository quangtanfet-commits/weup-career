# Slice 3: competency model + K-A-R progress (CP-8)

Mô hình năng lực 2 trục (ADR-013) — stacked trên #1 (base `feat/phase2-assessments`).

## Phạm vi
- **Cây 12 năng lực** (NL1–12, 3 lĩnh vực ABCD) + **indicators** K/A/R, gắn `competency_code` + `dieu5_code`.
- **LearnerProgress** (append-only) + **LearnerDomainPhase** (đa-phase cho `working`).
- **Endpoints:** `GET /competencies`, `GET /me/progress`, `POST /me/progress/indicators`.
- **CP-8:** độ sâu chỉ tiến K→A→R (rank monotonic), lịch sử append-only — chỉ ghi khi thực sự tiến.
- **2 trục:** `dev_phase` suy từ `school_level` (THCS→exploration, THPT→planning), cho phép lệch; nhãn VI "Nhận biết/Thực hiện-Vận dụng/Phản tư" (CTGDPT 2018).
- Seed 12 năng lực + 36 indicator (idempotent + CLI), wire `docker-entrypoint`.

## Đảm bảo 3 tầng
| | |
|---|---|
| Tests | **181 pass** (146 slice 1+2 + 35 mới), competency/* = **100%**, tổng 99% |
| CI gates | ruff check + **ruff format** + mypy --strict + **bandit -ll (0 issue)** đều sạch |
| Holdout (`competency-progress.feature`, app thật) | 5/6 scenario PASS; CP-8 no-regress verify trên app |
| **Gate B conformance (TLA+ trace)** | **CP-8** ✅ — replay `[AdvanceDepth 1,2,3]` (l=Len+1); sabotage `[3,1]` kẹt l=2 |

## Gaps (slice sau, không phải defect)
- **G-2:** `set_domain_phase` có ở service nhưng **chưa expose endpoint** → set dev_phase qua API (working multi-phase / [CRED_43DA9CCB]-deviation) chưa đạt. Read-side đa-phase đã hoạt động.
- Liên kết indicator ↔ assessment/activity tự động (FR-22) mới ở mức ghi thủ công.
- Hiển thị tiến bộ cho guardian/counselor (FR-24).

Conventional commits, không AI attribution. `main` không đụng.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
