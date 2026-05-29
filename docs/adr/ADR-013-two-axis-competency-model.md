# ADR-013: Mô hình Năng lực 2 Trục (K-A-R × Giai đoạn phát triển)

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Engineering Team

---

## Context

WeUp Career tham chiếu 3 framework quốc tế (NCDG/Mỹ, ABCD/Úc, ECG/Singapore — xem [`career-frameworks-synthesis.md`](../research/career-frameworks-synthesis.md)). Phát hiện cốt lõi: chúng dùng **hai trục bị nhầm là một**:
- **NCDG K→A→R** là trục **độ sâu nhận thức** (Bloom) — *biết sâu đến đâu*.
- **ABCD/ECG Awareness→…→Planning** là trục **giai đoạn phát triển nghề** — *đang ở đâu trong hành trình*.

Hai trục **trực giao**. Gộp làm một sẽ mất khả năng vừa định vị hành trình vừa đo thuần thục.

## Decision

**Mô hình hóa năng lực trên 2 trục độc lập:**

1. **Cây năng lực:** 12 năng lực ABCD × 3 lĩnh vực (A/B/C) làm `Competency` gốc; mỗi node gắn `dieu5_codes[]` (ánh xạ TT 16/2026 Điều 5).
2. **Trục độ sâu (đo lường):** `Indicator.depth ∈ {K, A, R}` kiểu NCDG, ánh xạ "Nhận biết → Thực hiện/Vận dụng → Phản tư" của CTGDPT 2018; `LearnerProgress` lưu `(competency, depth_achieved)` — chỉ tiến, không lùi, lịch sử append-only (CP-8).
3. **Trục giai đoạn phát triển:** `dev_phase ∈ {awareness, exploration, planning}` (ECG). Học sinh: suy ra từ `school_level` (cho phép lệch cá nhân). Người đi làm: **nhiều `dev_phase` đồng thời theo domain** (phi tuyến ABCD) qua `LearnerDomainPhase`.
4. **Instrument tự đánh giá:** RIASEC + VIPS + MBTI gắn vào năng lực (chủ yếu NL1).

## Alternatives Considered
| Phương án | Verdict |
|---|---|
| Chỉ dùng 1 framework (vd chỉ ECG) | ❌ Mất lớp đo lường (NCDG) hoặc từ vựng năng lực (ABCD) |
| Gộp độ sâu & giai đoạn thành 1 thang | ❌ Mất khả năng đo thuần thục độc lập với định vị hành trình |
| 2 trục trực giao + cây 12 năng lực + crosswalk Điều 5 | ✅ Chọn — vừa nền quốc tế, vừa tuân thủ pháp lý |

## Consequences
- Mỗi `ContentItem`/`AssessmentItem` gắn **2 nhãn**: `dieu5_code` (pháp lý) + `competency_code` (pedagogical), cộng `depth` + `dev_phase` + `school_level`.
- Kiến trúc **bất biến khi mở rộng** segment: Tiểu học/người đi làm chỉ khác phân tầng, không đổi lõi 2 trục.
- Module Sức khỏe tinh thần (ABCD NL4) là năng lực hạng nhất (gắn TT 18/2025). Liên quan: [ADR-012](./ADR-012-ai-recommendation-governance.md); nền lý luận: `docs/research/career-frameworks-synthesis.md`.
