# ADR-011: Xử lý Dữ liệu Nhạy cảm (kết quả trắc nghiệm)

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Engineering Team

---

## Context

Kết quả trắc nghiệm định hướng (**RIASEC, VIPS, MBTI**) phản ánh tính cách/đời sống riêng tư ⇒ **dữ liệu nhạy cảm tiềm năng** theo Luật BVDLCN 91/2025 (xem [`legal-basis.md`](../legal/legal-basis.md) §6). Cần bảo vệ ở mức cao hơn dữ liệu thường: mã hóa, kiểm soát truy cập chặt, và **truy vết mọi lần đọc**.

## Decision

1. **Mã hóa trường ở tầng ứng dụng (Field Crypto):** `AssessmentResult.result_payload` mã hóa trước khi ghi bằng `FIELD_ENCRYPTION_KEY` (tách khỏi `SECRET_KEY`), gắn `key_version` để hỗ trợ xoay khóa/re-encrypt. `is_sensitive=true` mặc định.
2. **Audit bắt buộc mọi lần đọc:** mọi truy cập kết quả đi qua một service ghi `audit_log(is_sensitive_access=true)` **trong cùng giao dịch** — không đường đọc nào bỏ qua audit. **Fail-closed** nếu ghi audit thất bại.
3. **Không lộ qua kênh phụ:** không log nội dung; không cache lâu/ở localStorage; không index trên nội dung kết quả; sự kiện/message chỉ mang id+loại.
4. **Quyền chủ thể dữ liệu:** xuất/xóa kết quả (trẻ <16 do guardian thực hiện); kết quả **versioned** (không ghi đè) để theo dõi thay đổi.

## Tính đúng đắn (TLA+)
`SensitiveDataAccess` chứng minh **CP-3** (mỗi đọc nhạy cảm ⇒ đúng 1 audit). Sabotage-check: thêm đường đọc không audit ⇒ TLC bắt vi phạm. Giám sát runtime: `sensitive_access_total == audit_writes_total`.

## Alternatives Considered
| Phương án | Verdict |
|---|---|
| Mã hóa toàn bộ DB (TDE) at-rest | ✅ Bổ sung tốt nhưng **không đủ**: không bảo vệ khi app/DB bị truy cập hợp lệ — vẫn cần field-level |
| Không mã hóa, chỉ RBAC | ❌ Không đạt mức bảo vệ cao cho dữ liệu nhạy cảm |
| Audit chỉ ghi write | ❌ Không truy vết được rò rỉ qua đọc |
| Field Crypto + audit mọi đọc | ✅ Chọn |

## Consequences
- Cần quy trình **backup khóa độc lập** với DB nhưng đồng bộ `key_version` (xem runbook Runbook 5/8).
- Mất khóa = mất khả năng giải mã ⇒ khóa là tài sản tối quan trọng (HSM/secret manager).
- Production ưu tiên PostgreSQL (audit/phân tích quy mô lớn). Liên quan: [ADR-010](./ADR-010-guardian-consent.md), [ADR-002](./ADR-002-database.md).
