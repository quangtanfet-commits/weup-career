# ADR-010: Kiến trúc Đồng ý Giám hộ cho người dùng <16

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Engineering Team

---

## Context

Một tỷ lệ đáng kể người dùng WeUp Career là **học sinh dưới 16 tuổi** (đặc biệt nhóm phân luồng sau THCS). Pháp luật VN (Luật BVDLCN 91/2025, NĐ 147/2024, Luật Trẻ em) yêu cầu **đồng ý của người đại diện theo pháp luật** trước khi xử lý dữ liệu cá nhân của trẻ. Đây là **ràng buộc cứng từ MVP**, không thể bổ sung sau (xem [`legal-basis.md`](../legal/legal-basis.md) §6).

## Decision

**Một `account_status` máy trạng thái + một Consent Guard tập trung chặn mọi route xử lý dữ liệu hướng nghiệp khi user `under_16` không có `GuardianConsent` active.**

- `age_band` suy ra từ `date_of_birth` khi đăng ký; `under_16` ⇒ `account_status = pending_guardian_consent`.
- `GuardianLink` phải `verified_at` qua **kênh độc lập** (email/VNeID) — **cấm self-consent**. Luồng phân tầng (VNeID HIGH/MEDIUM, email LOW) + chính sách mở khóa dữ liệu nhạy cảm: [`docs/security/guardian-verification.md`](../security/guardian-verification.md).
- Consent Guard là dependency đặt ở **tầng router** cho mọi route dữ liệu hướng nghiệp (assessment, recommendation, progress) — một điểm kiểm soát duy nhất.
- Thu hồi consent ⇒ dừng xử lý **mới** ngay (không xóa dữ liệu cũ — đó là quyền xóa riêng).

## Tính đúng đắn (TLA+)
Mô hình `ConsentLifecycle` chứng minh **CP-1** (không xử lý dữ liệu <16 khi consent ≠ active) và **CP-2** (thu hồi dừng xử lý mới). Sabotage-check: bỏ guard ⇒ TLC bắt vi phạm.

## Alternatives Considered
| Phương án | Verdict |
|---|---|
| Kiểm tra consent rải rác ở từng handler | ❌ Dễ sót đường vòng; không chứng minh được |
| Chặn ở frontend | ❌ Không đủ; client không tin cậy |
| Bổ sung consent sau MVP | ❌ Vi phạm pháp lý ngay từ người dùng <16 đầu tiên |
| Consent Guard tập trung ở router | ✅ Một điểm kiểm soát, kiểm chứng được bằng TLC |

## Consequences
- Vai trò `guardian` là **bắt buộc** từ MVP (không phải tính năng phụ).
- Trẻ <16 vẫn xem được **nội dung công khai** (thư viện nghề) khi chờ consent — chỉ chặn xử lý dữ liệu cá nhân.
- Claim JWT mang `age_band`/`account_status` để quyết nhanh, nhưng route nhạy cảm xác thực lại consent với DB.
- Liên quan: [ADR-011](./ADR-011-sensitive-data.md), [ADR-008](./ADR-008-security-controls.md).
