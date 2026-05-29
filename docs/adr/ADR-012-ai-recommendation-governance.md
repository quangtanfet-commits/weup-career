# ADR-012: Quản trị Gợi ý AI (Human-in-the-loop, giải thích, công bằng)

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Engineering Team

---

## Context

Lõi giá trị của WeUp Career là **gợi ý ngành/nghề/lộ trình** dựa trên trắc nghiệm + hồ sơ + tiến bộ năng lực. Đây gần như chắc chắn là **hệ thống AI thuộc Luật 134/2025**, tác động tới định hướng tương lai của trẻ vị thành niên ⇒ rủi ro **TRUNG BÌNH→CAO**. Ràng buộc pháp lý: **con người làm trung tâm** (Đ.4), **không thiên lệch**, **minh bạch/giải thích được**; cộng nguyên tắc **không ép buộc phân luồng** (TT 16/2026). Xem [`legal-basis.md`](../legal/legal-basis.md) §7.

## Decision

**Recommendation Engine tách thành ranh giới riêng, chỉ sinh "đề xuất + lý do"; con người ra quyết định cuối.**

1. **rationale bắt buộc:** không tạo được `Recommendation` nếu `rationale` rỗng (CP-6).
2. **Human-in-the-loop:** `Recommendation` khởi tạo `status=proposed`, `requires_human_confirmation=true`; chỉ **người** (student/guardian/counselor) chuyển sang accepted/rejected/deferred; hệ thống **không** tự áp dụng phân luồng (CP-5).
3. **Bias testing là gate riêng:** kiểm thử công bằng theo giới/vùng/hoàn cảnh định kỳ; vượt ngưỡng ⇒ fail CI; RIASEC/MBTI **không khóa cứng** lựa chọn theo định kiến (NFR-12).
4. **Truy vết giải trình:** lưu input → gợi ý → ai xác nhận/quyết định gì (audit).
5. **Phân loại rủi ro + DPIA** trước phát hành (Gate C).

## Tính đúng đắn (TLA+)
`RecommendationGovernance` chứng minh **CP-5** (chỉ người chuyển trạng thái có hiệu lực) và **CP-6** (luôn có rationale). Lưu ý: TLC chứng minh *quy trình*, **không** chứng minh gợi ý công bằng — đó là việc của bias testing.

## Alternatives Considered
| Phương án | Verdict |
|---|---|
| Auto-phân luồng theo điểm trắc nghiệm | ❌ Vi phạm "không ép buộc" + Luật 134/2025 |
| Gợi ý không kèm lý do (black-box) | ❌ Vi phạm minh bạch AI |
| Engine nhúng trong service chính | ❌ Khó cô lập ranh giới governance/bias |
| Engine tách + human-in-the-loop + rationale + bias gate | ✅ Chọn |

## Consequences
- UI luôn hiển thị lý do + "quyết định thuộc về bạn/giám hộ/GV"; không có nút "tự áp dụng".
- Cần pipeline bias testing + báo cáo đính kèm mỗi release.
- Để ngỏ adapter CSDL quốc gia GD&ĐT / thị trường lao động cho dữ liệu đầu vào. Liên quan: [ADR-013](./ADR-013-two-axis-competency-model.md), [ADR-008](./ADR-008-security-controls.md).
