# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

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
