# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added — Triển khai Backend (8 slice, kiến trúc hexagonal)
- **Slice 1 — Auth & Guardian consent** (consent gate <16, JWT HS256 access 15′ + refresh opaque)
- **Slice 2 — Assessments** (RIASEC / VIPS / MBTI; dữ liệu nhạy cảm mã hóa at-rest + audit log)
- **Slice 3/4 — Competency two-axis model** (12 năng lực ABCD × 3 area, đo K-A-R × dev_phase awareness/exploration/planning)
- **Slice 5 — Recommendation governance** (AI gợi ý human-in-the-loop, PR #10)
- **Slice 6 — School / lớp / học sinh** (PR #11)
- **Slice 7 — Admin / content / wellbeing** (PR #12)
- **Slice 8 — Account & data rights** (quyền chủ thể dữ liệu BVDLCN, PR #13)
- **Careers** — thư viện nghề ILO Việt Nam
- **Gate B harness** — instrument NDJSON trace cho conformance replay

### Added — Triển khai Frontend (8 slice tính năng, Next 16 App Router)
- f1-foundation (PR #17/#22) · f2-public-content (PR #23) · f3-assessment (PR #26)
- f4-competency (PR #25) · f5-recommendations (PR #27) · f6-wellbeing (PR #24)
- f7-counselor (PR #29) · f8-admin-editor (PR #28)
- Storybook + Chromatic visual regression (PR #31)

### Added — Bảo mật (hardening sau pentest weup-saas-20260531)
- **H-01** — Access-token JTI denylist khi logout, thu hồi token còn hạn (PR #36) → khắc phục PT-01
- **H-02** — Session-version epoch, vô hiệu hóa hàng loạt access token khi re-login/đổi mật khẩu (PR #37) → khắc phục PT-02
- **H-03** — Security headers + rate limiting trên auth endpoints (PR #38, fix E2E ratelimit PR #49) → khắc phục PT-03, PT-05

### Added — Kiểm chứng hình thức
- TLA+ 6 module ↔ CP-1…CP-8; Gate A (model check) + Gate B (conformance trace replay) 6/6; sabotage-check 6/6 pass

### Changed — Nâng cấp major frontend (Dependabot held bumps, doc-first, 2026-06-01)
- Vitest 2 → 4 (PR #52) · Tailwind CSS 3 → 4 Oxide/Lightning (PR #53) · Next 15 → 16.2.6 + next-intl 4 + ESLint 9 flat config (PR #54)

### Changed
- **Tái thiết kế toàn bộ tài liệu thiết kế từ domain Todo (placeholder) sang domain Hướng nghiệp Quốc gia WeUp Career.**
  - `docs/spec.md` v2.0.0 — NLSpec hướng nghiệp, neo vào TT 16/2026 Điều 5; 8 thuộc tính đúng đắn (CP-1…CP-8)
  - Kiến trúc (overview/data-flow/sequence/state/deployment) — entities & flows hướng nghiệp; consent <16, dữ liệu nhạy cảm, gợi ý human-in-the-loop
  - Security (threat-model/auth-design) — STRIDE + mối đe dọa AI/đạo đức; Consent Guard, RBAC quan hệ, mã hóa trường nhạy cảm
  - Testing/Scalability/UX/Operations — cập nhật theo domain + bias testing + vận hành dữ liệu nhạy cảm/consent/audit
  - TLA+ spec design v2.0.0 — 6 module ánh xạ CP-1…CP-8
  - ADR-001…009 cập nhật cho domain

### Added
- **Nền tảng domain:**
  - `docs/research/career-frameworks-synthesis.md` — tổng hợp 3 framework NCDG/ABCD/ECG; mô hình năng lực 2 trục; crosswalk Điều 5
  - `docs/legal/legal-basis.md` + `docs/research/sources.md` — căn cứ pháp lý & thư viện nguồn VN
- **4 ADR mới (đặc thù hướng nghiệp):**
  - ADR-010 Kiến trúc đồng ý giám hộ <16 · ADR-011 Xử lý dữ liệu nhạy cảm
  - ADR-012 AI Recommendation Governance · ADR-013 Mô hình năng lực 2 trục
- Hạ tầng kỹ thuật Phase 1 (C4, CI/CD, quality gates, Docker) — tái sử dụng từ thiết kế ban đầu

---

[Unreleased]: https://github.com/org/weup-career/compare/HEAD
