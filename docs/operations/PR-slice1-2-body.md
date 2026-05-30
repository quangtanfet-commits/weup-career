# Slices 1–2: auth + guardian consent + assessments (legal core)

Nền tảng Hướng nghiệp Quốc gia WeUp Career — hai slice đầu của backend, kèm bộ tài liệu thiết kế domain hướng nghiệp và bằng chứng đảm bảo 3 tầng.

## Phạm vi
- **Slice 1 — auth + guardian consent (lõi pháp lý):** đăng ký + cổng tuổi, JWT + refresh xoay vòng, cổng đồng ý giám hộ <16 (CP-1/CP-2), RBAC quan hệ (CP-4), audit, field-crypto, hexagonal.
- **Slice 2 — assessments (RIASEC/VIPS/MBTI):** trắc nghiệm dữ liệu nhạy cảm mã hóa at-rest, CP-3 (audit mọi lần đọc, fail-closed), CP-1 wiring thật, bias M1 (scorer answers-only), assurance gate (FF-19), seed instrument idempotent + CLI.
- **Tài liệu:** spec v2 (8 CP), 13 ADR, architecture/security/testing/scalability/ux/operations, research synthesis 3 framework, legal-basis + DPIA, bias-testing, guardian-verification, validate-design evidence pack.

## Đảm bảo 3 tầng
| | Slice 1 | Slice 2 |
|---|---|---|
| Tests | 100, 100% critical | 146, 100% assessments + path nhạy cảm |
| Holdout (app thật) | ship 96.2 | ship 99.5 |
| Gate B conformance (TLA+ trace) | CP-1, CP-2 | CP-1 artifact (non-vacuous), CP-7 |

- mypy --strict + ruff sạch; Gate A: 6 module TLC CP-1…CP-8 + 6/6 sabotage.
- Neo pháp lý: TT 16/2026 Điều 5, BVDLCN 91/2025, Luật AI 134/2025.

## Tuân thủ holdout
`scenarios/` là holdout — coder build chỉ đọc `docs/spec.md`, không xem `scenarios/`. Holdout chạy sau build (`.last-run.json`).

## Ghi chú trung thực
- `docker compose up` chưa kiểm được (DinD sandbox lỗi); verify tương đương bằng native (alembic + uvicorn) + in-process ASGI.
- Gate B token (CP-7) ở phạm vi **một phiên**; impl cho đa-phiên (ngoài model hiện tại — xem GATE_B_CONFORMANCE.md).
- Còn lại: competency/reco/careers/counseling (slice sau); VNeID thật → đổi `SENSITIVE_MIN_ASSURANCE` sang `medium`.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
