# Architecture Fitness Functions — WeUp Career

> Mỗi **lời hứa cấu trúc** của hệ thống → một test CI **fail nếu bị vi phạm**. Tên test = tên lời hứa. Nguồn: `docs/spec.md`, ADR-001…013, `docs/formal-verification/`.
>
> Trạng thái: **catalogue** (mệnh đề + cơ chế enforce). Test thực thi tạo cùng lúc với implementation (ruflo `coder`+`tester`). Mục nào chưa enforce được đánh dấu **GAP** + punch-list id.

## Quy ước
- **Build-time**: linter / [CRED_E4BD0FCC] / [CRED_3DB17BA0] check.
- **Test-time**: integration/property test assert tính chất cấu trúc.
- **Runtime**: metric Prometheus + alert.

| # | Lời hứa (claim) | Loại | Cơ chế enforce | Nguồn | Trạng thái |
|---|---|---|---|---|---|
| FF-01 | Trẻ <16 không có consent active KHÔNG xử lý được dữ liệu hướng nghiệp | Test-time | Integration: mọi route career-data trả 403 GUARDIAN_CONSENT_REQUIRED khi `age_band=under_16 ∧ consent≠active` | CP-1, ADR-010 | catalogue |
| FF-02 | Thu hồi consent dừng xử lý mới | Test-time | Integration: sau revoke, submit → 403 | CP-2 | catalogue |
| FF-03 | Mỗi đọc kết quả nhạy cảm sinh đúng 1 audit | Test-time + Runtime | Test đếm audit trước/sau; metric `sensitive_access_total == audit_writes_total` + alert khi lệch | CP-3, ADR-011 | catalogue |
| FF-04 | Kết quả trắc nghiệm mã hóa at-rest (không plaintext trong DB) | Test-time | Query thẳng cột `result_payload`, assert không chứa nhãn kết quả đọc được | ADR-011 | catalogue |
| FF-05 | Không truy cập chéo trừ quan hệ được cấp quyền | Test-time | Integration: cross-user→404, counselor↔trường khác→403, guardian↔trẻ chưa-link→403/404 | CP-4, ADR-008 | catalogue |
| FF-06 | Không gợi ý nào thiếu rationale | Test-time + Build | DB constraint `rationale NOT NULL`; test cố tạo rationale rỗng→fail | CP-6, ADR-012 | catalogue |
| FF-07 | Không gợi ý nào có hiệu lực khi chưa người xác nhận | Test-time | Không tồn tại endpoint auto-apply; test trạng thái proposed không đổi lộ trình | CP-5 | catalogue |
| FF-08 | Refresh token thu hồi không tái dùng; tối đa 1 active/user | Test-time | Integration: dùng RT đã revoke→401; property: không hai token active | CP-7 | catalogue |
| FF-09 | Độ sâu năng lực không lùi (K→A→R) | Test-time | Property (Hypothesis): chuỗi advance ngẫu nhiên ⇒ depth không giảm | CP-8 | catalogue |
| FF-10 | KHÔNG log PII/kết quả nhạy cảm/token | Build + Test | Semgrep rule cấm log trường nhạy cảm; test scan output log của request trắc nghiệm | NFR-06/10 | catalogue |
| FF-11 | Gợi ý/[CRED_F931E5D8] công bằng theo giới/vùng/hoàn cảnh | Test-time (gate riêng) | Bias test M1–M5 (counterfactual ≥99%, DIR≥0.80); job `bias-test` wired path-filtered ⇒ fail CI khi vượt ngưỡng — [`docs/testing/bias-testing.md`](../../testing/bias-testing.md) | NFR-12, ADR-012 | ✅ khung + CI wired (execution chờ engine) |
| FF-12 | Hexagonal: service không import router; repo không import service | Build-time | import-linter (Python) / [CRED_24A88AD2] rule | ADR-009 | catalogue |
| FF-13 | Mọi `content_item`/`assessment_item` gắn ĐỦ `dieu5_code` + `competency_code` | Build/Test | DB NOT NULL + check constraint; test seed-data validation | ADR-013, Điều 5 | catalogue |
| FF-14 | Chỉ dùng license cho phép (permissive) | Build-time | `pip-licenses`/`license-checker` allowlist | engineering-playbook | catalogue |
| FF-15 | Coverage 100% trên consent/sensitive/auth/reco | Test-time | pytest-cov per-module fail-under=100 cho các path đó | NFR-19 | catalogue |
| FF-16 | OpenAPI schema ổn định (đổi có chủ đích) | Build-time | `openapi-spec-validator` + diff gate | ADR-003 | catalogue |
| FF-17 | TLC CP-1…CP-8 pass khi đổi state machine | Build-time | CI job `formal-verify` (đã trỏ 6 module) | TLC report | ✅ wired |
| FF-18 | Nội dung versioned + gắn `school_level` (rà soát định kỳ) | Test-time | Test: content có version & school_level; job nhắc rà soát | TT 16/2026, ADR-002 | catalogue |
| FF-19 | Dữ liệu nhạy cảm trẻ <16 chỉ xử lý khi `assurance_level ≥ MEDIUM` | Test-time | Integration: assurance=low + submit→403; ≥medium→cho phép | P-4, [`guardian-verification.md`](../../security/guardian-verification.md) | catalogue |

## Wiring
- Build/Test FF chạy trong `.github/workflows/ci.yml` (đã có gate test/lint/semgrep/TLC). Thêm: bias job (FF-11, P-1), import-linter (FF-12), license check (FF-14), log-scan (FF-10).
- Runtime FF-03 cần expose `/metrics` (`sensitive_access_total`, `audit_writes_total`) + alert rule.
- Mỗi FF khi triển khai đặt tên test = id ở trên (vd `test_FF01_under16_blocked_without_consent`).
