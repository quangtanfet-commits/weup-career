# ADR-016: Khung năng lực & tự đánh giá Tư vấn viên

**Status:** Proposed
**Date:** 2026-06-04
**Deciders:** Engineering Team
**Liên quan:** đề xuất `docs/proposals/cross-research-career-guidance-proposal.md` (P1); `docs/research/career-frameworks-synthesis.md`; ràng buộc `docs/legal/legal-basis.md` (TT 18/2025 — tư vấn học đường); spec `docs/spec.md` §2, §3.11, §5.

---

## Context

Nghiên cứu đối chiếu (R-8) và `career-frameworks-synthesis.md` nêu: **tư vấn viên hướng nghiệp cần một khung năng lực để tự đánh giá** và xác định lộ trình phát triển nghề nghiệp của chính họ. Đây là khoảng trống thực thi lớn (R-10): chất lượng Tier 3 (tư vấn cá nhân, FR-81) phụ thuộc trực tiếp vào năng lực counselor.

Hiện trạng dự án:
- `counselor` đã tồn tại như **actor** (spec §2) và vận hành `CounselingSession` (FR-82), nhưng
- **không** có khung năng lực cho **chính tư vấn viên**. Cây 12 năng lực (NL1–NL12) hiện hành chỉ dành cho **người học** — không tái dụng cho counselor vì khác hoàn toàn về bản chất (năng lực hành nghề tư vấn vs. năng lực hướng nghiệp của học sinh).

Ràng buộc: không được làm nhiễu mô hình lõi của người học, không đụng các bất biến CP-1..CP-8.

## Decision

**Mô hình hóa khung năng lực tư vấn viên thành một module ĐỘC LẬP, tách hoàn toàn khỏi cây 12 năng lực người học.**

1. **Entity riêng, không tái dụng `Competency` người học:**
   - `CounselorCompetency` — định nghĩa năng lực hành nghề tư vấn (vd: đạo đức nghề, kỹ năng lắng nghe, hiểu công cụ trắc nghiệm, an toàn dữ liệu/BVDLCN, nhận biết dấu hiệu cần chuyển tuyến).
   - `CounselorSelfAssessment` — bản tự đánh giá của một counselor tại một thời điểm, gồm điểm tự xếp theo từng năng lực + lộ trình phát triển gợi ý.
2. **Tự đánh giá, không phải bị-chấm.** Đây là công cụ **phát triển bản thân** của counselor (self-assessment), không phải KPI/đánh giá hành chính do school_admin áp xuống ở MVP — tránh biến thành công cụ giám sát.
3. **Phạm vi dữ liệu tách bạch:** dữ liệu tự đánh giá của counselor **không** trộn với dữ liệu hướng nghiệp của học sinh; không nằm trong phạm vi consent giám hộ (CP-1) vì không liên quan trẻ.
4. **Gợi ý lộ trình phát triển** cho counselor có thể tái dụng cơ chế giải thích của Recommendation Engine **nhưng** là luồng riêng — KHÔNG đụng CP-5/CP-6 (vốn ràng buộc gợi ý phân luồng cho người học).
5. **Căn cứ pháp lý:** gắn TT 18/2025 (công tác tư vấn tâm lý/hướng nghiệp học đường) làm nền cho nội dung khung năng lực.

## Alternatives Considered

| Phương án | Verdict |
|---|---|
| Tái dụng cây 12 năng lực người học cho counselor | ❌ Sai bản chất; ô nhiễm mô hình lõi; rủi ro lẫn dữ liệu học sinh/counselor |
| Để counselor competency ngoài hệ thống (tài liệu giấy) | ❌ Không đo được, không gắn vào quy trình Tier 3, lặp lại khoảng trống R-10 |
| Module độc lập + entity riêng + self-assessment | ✅ Chọn — không đụng lõi/CP-*, đo được, đúng tinh thần R-8 |

## Consequences

- **Tích cực:** Nâng chất lượng Tier 3 có cơ sở đo; module cộng thêm, không sửa lõi (đúng G-07); không chạm bất biến CP-1..CP-8.
- **Đánh đổi:** Thêm bề mặt dữ liệu/API mới; cần nội dung khung năng lực chuẩn (nguồn TT 18/2025 + tài liệu nghề tư vấn) trước khi có giá trị thực.
- **Phạm vi:** **MVP = spec + ADR + data model**; UI tự đánh giá có thể Phase 2 (đề xuất P1 §3).
- **Quyền riêng tư:** Dữ liệu tự đánh giá của counselor là dữ liệu cá nhân của họ → tuân BVDLCN; nếu sau này cho school_admin xem tổng hợp, **phải qua DPIA cập nhật** trước.
- **Chưa hiện thực:** ADR ở trạng thái **Proposed**; FR §3.11 + entity đánh dấu *v2.1 — spec, chưa hiện thực*.
