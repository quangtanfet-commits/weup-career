# ADR-015: Cấu trúc hóa Labor Market Intelligence (LMI)

**Status:** Proposed
**Date:** 2026-06-04
**Deciders:** Engineering Team
**Liên quan:** đề xuất `docs/proposals/cross-research-career-guidance-proposal.md` (P2); ràng buộc `docs/legal/legal-basis.md`; spec `docs/spec.md` §3.4, §5.

---

## Context

TT 16/2026/TT-BGDĐT yêu cầu cổng hướng nghiệp cung cấp **thông tin xu hướng thị trường lao động (TTLĐ)** như một trong các trụ hạ tầng số, phục vụ chống **skills-mismatch**. Nghiên cứu đối chiếu (`docs/temp/cross-research-report-career-guiding.md`, R-3(2)/R-6) nhấn LMI là **lõi**, không phải tiện ích phụ.

Hiện trạng dự án: `CareerProfile.labor_market_outlook` chỉ là **một field văn bản tự do**, không cấu trúc, không nguồn, không thời điểm. Không thể lọc nghề theo cầu lao động, không thể rà soát/cập nhật định kỳ có kỷ luật (NFR-26), không truy vết được xuất xứ số liệu.

Ràng buộc cứng:
- **NG-02:** WeUp Career **không** sở hữu/không trở thành nền tảng tuyển dụng; dữ liệu TTLĐ động tích hợp qua **adapter giai đoạn sau** (HTTT TTLĐ quốc gia — Luật 74/2025 Đ.19).
- **Chất lượng nguồn:** báo cáo nghiên cứu có toàn bộ citations hỏng (`[object Object]` ×72) và số liệu chưa kiểm chứng → **cấm** đưa số liệu từ báo cáo đó vào dataset. Mọi điểm dữ liệu phải có `source_ref` thật + `as_of_date`.

## Decision

**Cấu trúc hóa LMI thành thực thể hạng nhất `LaborMarketSnapshot`, tách khỏi field văn bản tự do, với xuất xứ bắt buộc.**

1. **Entity mới `LaborMarketSnapshot`** (xem spec §5) với các trường có cấu trúc: `sector` (ngành), `salary_range`, `demand_forecast`, `required_skills[]`, `region`, **`source_ref` (NOT NULL)**, **`as_of_date` (NOT NULL)**, `version`.
2. **`source_ref` + `as_of_date` BẮT BUỘC** ở tầng schema — không cho phép tạo snapshot không xuất xứ/không thời điểm. Đây là hàng rào chống "mượn" số liệu chưa kiểm chứng.
3. **MVP = dataset tĩnh, có tuyển chọn, có nguồn.** Khởi đầu **khung rỗng** (không có dữ liệu giả). Chỉ nạp khi có nguồn thẩm quyền (HTTT TTLĐ quốc gia / báo cáo ngành chính thức). Nội dung tuyển chọn này là **nội dung do dự án sở hữu**, không phải "sở hữu dữ liệu TTLĐ" → **không vi phạm NG-02**.
4. **Giai đoạn sau = adapter động** tới HTTT TTLĐ quốc gia (giữ nguyên NG-02 + NFR-25 data residency). `LaborMarketSnapshot` là lớp đệm trung gian ổn định để adapter ghi vào.
5. **Liên kết `CareerProfile` → `LaborMarketSnapshot`** (theo `sector`), bồi cho FR-32 (lọc/sắp xếp nghề theo cầu lao động). Giữ `labor_market_outlook` như tóm tắt người-đọc, nhưng số liệu định lượng chuyển sang snapshot có nguồn.
6. **Cadence rà soát** gắn NFR-26 (content governance): snapshot có `as_of_date` → quy trình đánh dấu "quá hạn" khi vượt ngưỡng tuổi dữ liệu.

## Alternatives Considered

| Phương án | Verdict |
|---|---|
| Giữ `labor_market_outlook` văn bản tự do | ❌ Không lọc/đo/rà soát được; không truy vết nguồn; trái tinh thần R-3(2) |
| Nạp ngay dataset từ báo cáo nghiên cứu | ❌ Vi phạm kỷ luật nguồn — citations hỏng, số liệu chưa kiểm chứng |
| Tích hợp adapter động ngay ở MVP | ❌ Phình phạm vi; HTTT TTLĐ quốc gia chưa sẵn sàng; trái lộ trình NG-02 |
| Entity có cấu trúc + `source_ref`/`as_of_date` bắt buộc, dataset tĩnh có nguồn, adapter sau | ✅ Chọn — cấu trúc hóa được, giữ NG-02, ép kỷ luật xuất xứ |

## Consequences

- **Tích cực:** Lọc/sắp xếp nghề theo cầu lao động khả thi; rà soát định kỳ có kỷ luật (NFR-26); xuất xứ minh bạch; adapter động cắm vào sau không phải đổi schema.
- **Đánh đổi:** MVP có thể **khung rỗng/ít dữ liệu** cho tới khi có nguồn thẩm quyền — chấp nhận, vì thà thiếu còn hơn sai. UI phải xử lý trạng thái "chưa có dữ liệu TTLĐ cho ngành này".
- **Bất biến giữ nguyên:** CP-1..CP-8 không đụng. Cây 12 năng lực + 2 trục bất biến. NG-02/NFR-25 giữ.
- **Chưa hiện thực:** ADR này ở trạng thái **Proposed**; FR + entity tương ứng đánh dấu *v2.1 — spec, chưa hiện thực* trong spec.md cho tới khi được duyệt triển khai.
