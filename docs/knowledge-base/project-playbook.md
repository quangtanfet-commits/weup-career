# Project Playbook — WeUp Career

**Một câu:** Nền tảng Hướng nghiệp quốc gia cho học sinh THCS/THPT và người đi
làm tại Việt Nam — KHÔNG phải Todo app (đó là placeholder cũ).

## Đối tượng & phạm vi

- **MVP:** THCS + THPT trước; mở rộng người đi làm sau.
- **Đo lường:** mô hình **K+A+R** (Knowledge + Attitude + Result).
- **Công cụ trắc nghiệm:** RIASEC + VIPS + MBTI; mô hình 2 trục.
- **Vai trò:** student / working (toàn cục qua `user_type`); counselor /
  school_admin (DB-relational theo trường, KHÔNG phải cờ toàn cục);
  content_editor (cờ toàn cục `is_content_editor`). **Không có superadmin.**

## Ràng buộc pháp lý (cứng)

- Trẻ **<16 tuổi** đăng ký phải qua **người giám hộ** (guardian consent).
- Tuân thủ **Luật Bảo vệ Dữ liệu Cá nhân 2025** + **Luật Việc làm 2025**
  (hiệu lực 2026). Chi tiết: `docs/legal/legal-basis.md`.
- Hệ quả thiết kế: consent guard (CP-1/CP-2), field-level crypto (ADR-011),
  audit (CP-3), xác minh email (N-3) trước khi cho đăng nhập.

## Ngôn ngữ

- **Copy hướng tới người dùng: tiếng Việt.** Định danh kỹ thuật (code, biến,
  API, commit): **tiếng Anh.**

## Stack

- **Backend:** Python 3.12 · FastAPI · SQLAlchemy 2.0 async · Pydantic v2 ·
  Alembic · SQLite (aiosqlite, trừu tượng hoá cho PostgreSQL) · structlog · uv.
  Kiến trúc **hexagonal** (ports & adapters): service thuần logic, không import
  FastAPI; repository là Protocol port + adapter SQLAlchemy.
- **Frontend:** Next.js 16 (Turbopack) · React · Tailwind 4 · Vitest 4 ·
  Storybook + Chromatic · Playwright (3 trình duyệt) · axe-core.

## Ràng buộc môi trường (QUAN TRỌNG)

- Dev = **devcontainer aarch64/linuxkit, DinD** trên host Mac mini.
- **KHÔNG chạy được `docker compose` stack** ⇒ mọi service chạy **native**
  (uv / npm / playwright trực tiếp), không qua nginx.
- `net.ipv4.ip_unprivileged_port_start=0` ⇒ bind `:80`/`:443` không cần root.
- ASGI entrypoint là **factory**: `uv run uvicorn app.main:get_app --factory`
  (`app.main:app` KHÔNG tồn tại).
- VS Code Dev Containers tự forward listener → `localhost` của host.

## Bản đồ slice đã hoàn thành

- **Backend:** phase1 (legal core auth+consent) → phase2 assessments →
  phase3 competency → phase4 careers → slice5 reco-engine →
  slice6 school-counseling → slice7 admin-content-wellbeing →
  slice8 account-data-rights.
- **Frontend:** F1 foundation → F2 public-content → F3 assessment →
  F4 competency → F5 recommendations → F6 wellbeing → F7 counselor →
  F8 admin-editor.
- **Bảo mật:** H-01 (access-token denylist), H-02 (session-version epoch),
  H-03 (HTTP hardening), N-3 (email verification), PT-04 (chống dò email),
  N-5 (jose→PyJWT), N-6 (SHA-pin actions).
- **Formal verification:** 6 họ TLA+ (xem `architecture-decisions.md`).
