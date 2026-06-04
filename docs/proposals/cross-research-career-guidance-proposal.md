# Đề xuất áp dụng — Đối chiếu nghiên cứu "Nền tảng hướng nghiệp quốc gia" với WeUp Career

**Trạng thái:** ĐỀ XUẤT (PROPOSAL) — *chưa* chỉnh sửa gì vào dự án. Chờ duyệt.
**Ngày:** 2026-06-04
**Nguồn nghiên cứu:** `docs/temp/cross-research-report-career-guiding.md` (GOAP 7 bước, 72 data point, tạo 2026-06-01)
**Đối chiếu với:** `docs/spec.md` v2.0.0, `docs/legal/legal-basis.md`, `docs/research/career-frameworks-synthesis.md`
**Người viết:** Engineering (Claude)

---

## 0. TL;DR — Kết luận nhanh

1. **Dự án KHÔNG đi sau nghiên cứu.** Spec v2.0.0 (viết 2026-05-29) đã tham chiếu sâu **TT 16/2026/TT-BGDĐT Điều 5** và đã hiện thực hóa đủ 5 nội dung (a/b/c/d/đ). Nghiên cứu này **phần lớn xác nhận** hướng đi hiện tại, không lật ngược.
2. **Số điểm thực sự MỚI là ít nhưng có giá trị.** Tập trung ở 6 ứng viên: (P1) Khung năng lực **tư vấn viên**, (P2) Nâng tầm **Labor Market Intelligence**, (P3) Làm giàu **module trải nghiệm nghề**, (P4) **Công bằng vùng sâu/offline/đa ngôn ngữ dân tộc**, (P5) **Kênh giao tiếp phụ huynh**, (P6) **Mô hình hệ sinh thái đối tác** (trường–ĐH–GDNN–doanh nghiệp).
3. **Cảnh báo chất lượng nguồn (đọc kỹ §5).** Báo cáo nghiên cứu là tự sinh; toàn bộ phần Citations bị hỏng (`[object Object]` ×72), và nhiều "số liệu" (ngày ban hành TT, '19 Train' 500 HS/30k reach, 80 trainer/2.700 GV) **chưa kiểm chứng**. `legal-basis.md` mới là nguồn pháp lý có thẩm quyền của dự án — nghiên cứu chỉ là nguồn **bổ trợ/đối chiếu**.
4. **Khuyến nghị:** Áp dụng P1–P4 ở mức **spec/ADR + dataset tĩnh MVP**; P5–P6 đưa vào **roadmap giai đoạn sau**. Không điểm nào đòi viết lại lõi (cây 12 năng lực + 2 trục vẫn bất biến).

---

## 1. Tóm tắt nghiên cứu (phân tích chi tiết)

Nghiên cứu chạy quy trình GOAP 7 bước (Goal → State → Web search → Document → Synthesis → Insight → Verification) quanh đề bài "nền tảng hướng nghiệp quốc gia". Các **luận điểm cốt lõi** rút ra:

| # | Chủ đề nghiên cứu | Nội dung chính |
|---|---|---|
| R-1 | **Khung pháp lý TT 16/2026** | Thông tư hướng nghiệp & phân luồng, áp dụng xuyên Tiểu học → THCS → THPT; bắt buộc phối hợp giữa trường phổ thông, ĐH, GDNN, tổ chức, doanh nghiệp. (Nghiên cứu nêu ngày ký 24/3/2026 — *cần kiểm chứng*.) |
| R-2 | **Cổng thông tin hướng nghiệp quốc gia** | Trường phải lập & vận hành cổng thông tin: nghề nghiệp, xu hướng TTLĐ, lộ trình học, học liệu. Cổng **phải bảo đảm an toàn thông tin & BVDLCN** trong thu thập/lưu trữ/sử dụng. |
| R-3 | **4 trụ hạ tầng số** | (1) Portal thông tin nghề; (2) **Labor Market Intelligence** (job data, lương, dự báo việc làm); (3) công cụ AI (đánh giá năng lực, khảo sát sở thích, hướng dẫn trải nghiệm, lập kế hoạch nghề, tư vấn online); (4) **bảo mật & BVDLCN**. |
| R-4 | **Hệ sinh thái đa bên** | Trường phổ thông là đầu mối điều phối ĐH/GDNN/TT học tập suốt đời/doanh nghiệp; đội triển khai gồm quản lý trường, GV, tư vấn viên, GV nghề, giảng viên ĐH, chuyên gia DN, đại diện địa phương. |
| R-5 | **Mô hình giao nhận tích hợp** | Tích hợp vào chương trình GDPT + đa dạng hình thức: lớp học, hoạt động trải nghiệm, ngoại khóa, tư vấn; **cả trực tiếp lẫn online**. |
| R-6 | **Labor Market Intelligence theo ngành nóng** | Tập trung công nghệ cao, kinh tế xanh, AI, TMĐT, chuỗi cung ứng; xu hướng 2026: gig economy, reskilling nhanh, chuẩn lao động đổi, khan hiếm nhân tài. Giải quyết **skills-mismatch**. |
| R-7 | **Công bằng & tiếp cận** | Bắt buộc phủ toàn quốc, đặc biệt **vùng sâu/nông thôn**: CSDL truy cập qua mobile, công cụ tư vấn online, **hỗ trợ đa ngôn ngữ**, học liệu số + máy tính có internet ở trường vùng xa. |
| R-8 | **Phát triển đội ngũ tư vấn** | Tư vấn viên cần **khung năng lực để tự đánh giá** & xác định lộ trình phát triển. (Số liệu 80 trainer / 2.700 GV — *cần kiểm chứng*.) AI hỗ trợ GV thiết kế hoạt động (aptitude test, mô phỏng nghề). |
| R-9 | **Phân tầng theo cấp học** | Tiểu học: hình thành nhận thức nghề qua trải nghiệm; THCS/THPT: nâng chất lượng gắn lộ trình sau tốt nghiệp. 5 thành phần cốt lõi (= Điều 5 a–đ). |
| R-10 | **Khoảng trống thực thi** | Trường gặp khó: phối hợp đối tác ngoài kém hiệu quả; thiếu chủ động tạo cơ hội trải nghiệm; truyền thông/tư vấn cho HS & phụ huynh hạn chế; nội dung thiếu đa dạng. |
| R-11 | **Mô hình pilot cộng đồng** | '19 Train' (miền Trung): podcast, livestream chuyên gia, workshop ĐH, thực tập DN. ACCA 'Future Pathways' nối trường–ĐH–DN. (*Số liệu reach cần kiểm chứng.*) |

---

## 2. Đối chiếu: nghiên cứu ↔ dự án đã triển khai

Ký hiệu: ✅ đã có & đủ · 🟡 có một phần · ⛔ chưa có (gap)

| Chủ đề | Trạng thái dự án | Bằng chứng trong repo |
|---|---|---|
| R-1 Khung pháp lý TT 16/2026 Điều 5 | ✅ | `legal-basis.md §4.5`; spec G-01, FR gắn `dieu5_code` a–đ |
| R-2 Cổng thông tin quốc gia (định vị) | 🟡 | WeUp Career **chính là** cổng đó (spec §1) nhưng spec chưa định vị tường minh là "cổng quốc gia theo TT16"; an toàn TT/BVDLCN đã có (NFR-10/14/16) |
| R-3(1) Portal thông tin nghề | ✅ | FR-30..33 `CareerProfile`, versioned |
| R-3(2) **Labor Market Intelligence** | 🟡 | Chỉ là `labor_market_outlook` (1 field) + adapter "giai đoạn sau" (NG-02, NFR-25). Chưa có dataset/dự báo/ngành nóng có cấu trúc |
| R-3(3) Công cụ AI | ✅ | RIASEC/VIPS/MBTI (FR-10), Recommendation Engine có rationale (FR-60..63, CP-5/6) |
| R-3(4) Bảo mật & BVDLCN | ✅ | NFR-10/14/16, DPIA, CP-3/4, field-crypto ADR-011 |
| R-4 Hệ sinh thái đa bên | 🟡 | Có kênh trường B2B2C (FR-80..83) nhưng ĐH/GDNN/DN chưa là thực thể; chỉ Pathway `gdnn` + FR-31 nhánh trường nghề |
| R-5 Giao nhận tích hợp (online+trực tiếp) | ✅ | Web responsive; counselor Tier 1/2/3 (FR-81); trực tiếp = CounselingSession |
| R-6 LMI theo ngành nóng / xu hướng 2026 | 🟡 | Roadmap Phase 3 (working, SkillsFuture) đề cập; chưa có dữ liệu ngành nóng cho MVP |
| R-7 Công bằng vùng sâu/offline/đa ngôn ngữ | 🟡 | WCAG 2.1 AA, responsive 320px, i18n-ready vi (NFR-21/22/23). **Chưa** có: low-bandwidth/offline, **ngôn ngữ dân tộc thiểu số**, mobile-first vùng xa |
| R-8 **Khung năng lực tư vấn viên** | ⛔ | Có actor `counselor` nhưng **không** có khung tự đánh giá năng lực cho chính tư vấn viên. (Cây 12 năng lực hiện chỉ cho **người học**.) |
| R-9 Phân tầng theo cấp học | ✅ | Mô hình 2 trục dev_phase × K-A-R, `school_level` (FR-22/23, G-07) |
| R-10 Khoảng trống thực thi (giao tiếp phụ huynh, đa dạng nội dung) | 🟡 | Guardian có consent/xem hồ sơ (FR-03/24) nhưng **không** có kênh truyền thông/tư vấn chủ động cho phụ huynh; đa dạng nội dung chưa có chỉ số đo |
| R-11 Mô hình pilot/sự kiện cộng đồng | ⛔ | Không có thực thể Program/Event (podcast/livestream/workshop/thực tập) |

**Nhận định:** 7/13 chủ đề đã đủ ✅, 4/13 có một phần 🟡, chỉ 2/13 là gap thực sự ⛔ (khung năng lực tư vấn viên; program/event cộng đồng). Đây là tín hiệu tốt: nền tảng pháp lý–thiết kế của dự án vững, nghiên cứu chủ yếu **củng cố** chứ không phản bác.

---

## 3. Đề xuất áp dụng (ứng viên, theo ưu tiên)

> Mỗi đề xuất nêu: **Là gì · Vì sao (căn cứ) · Gắn vào đâu · Phạm vi MVP/sau · Công sức/Rủi ro**. Tất cả **chưa** được áp dụng.

### P1 — Khung năng lực & tự đánh giá cho Tư vấn viên (gap ⛔)
- **Là gì:** Một bộ khung năng lực nghề tư vấn hướng nghiệp + công cụ tự đánh giá + gợi ý lộ trình phát triển cho `counselor` (tách biệt với cây 12 năng lực của người học).
- **Vì sao:** R-8 + `career-frameworks-synthesis.md` đã nhắc tư vấn viên cần khung tự đánh giá; gắn TT 18/2025 (tư vấn học đường). Tăng chất lượng Tier 3 — đúng khoảng trống R-10.
- **Gắn vào đâu:** FR mới (nhóm 3.9); data model: `CounselorCompetency`, `CounselorSelfAssessment`. Không đụng lõi học sinh.
- **Phạm vi:** Spec + ADR ngắn ở MVP; UI có thể Phase 2.
- **Công sức/Rủi ro:** Trung bình / Thấp (module độc lập, không ảnh hưởng bất biến CP-*).

### P2 — Nâng tầm Labor Market Intelligence (🟡 → cấu trúc hóa)
- **Là gì:** Chuyển `labor_market_outlook` từ 1 field tự do thành **mô hình có cấu trúc**: ngành nóng (công nghệ cao, kinh tế xanh, AI, TMĐT, chuỗi cung ứng), dải lương, dự báo cầu, kỹ năng yêu cầu — kèm `source_ref` + `as_of_date` + chính sách rà soát.
- **Vì sao:** R-3(2)/R-6 nhấn LMI là **lõi** chống skills-mismatch, không phải "giai đoạn sau". Hợp NFR-26 (rà soát nội dung định kỳ).
- **Gắn vào đâu:** Mở rộng `CareerProfile`; thêm `LaborMarketSnapshot` (dataset **tĩnh** cho MVP, adapter động sau — giữ NG-02). Bồi cho FR-32 (lọc nghề theo cầu TTLĐ).
- **Phạm vi:** Dataset tĩnh "TTLĐ 2026" ở MVP; adapter HTTT TTLĐ quốc gia (Điều 19 Luật 74/2025) giai đoạn sau.
- **Công sức/Rủi ro:** Trung bình / Thấp–TB (rủi ro chính: nguồn dữ liệu lương/dự báo phải có xuất xứ — tránh số liệu nghiên cứu chưa kiểm chứng).

### P3 — Làm giàu Module Trải nghiệm nghề — Điều 5(d) (🟡)
- **Là gì:** Mở rộng `ContentItem` để hỗ trợ loại trải nghiệm: "một ngày làm nghề", **mô phỏng tương tác**, video/podcast, livestream chuyên gia; gắn NL5/NL9.
- **Vì sao:** R-5/R-6/R-11 + khoảng trống R-10 (thiếu trải nghiệm thực hành). FR-50/51 đã có khung, cần làm giàu kiểu nội dung.
- **Gắn vào đâu:** `ContentItem.type` (enum: article, simulation, video, podcast, livestream); FR-50 mở rộng.
- **Phạm vi:** Content type tĩnh MVP; kết nối DN/GDNN cho trải nghiệm thật giai đoạn sau (đã là FR-51).
- **Công sức/Rủi ro:** Thấp–TB / Thấp.

### P4 — Công bằng vùng sâu: low-bandwidth / offline-tolerant / đa ngôn ngữ dân tộc (🟡)
- **Là gì:** Bổ sung NFR: chịu băng thông thấp, tải nhẹ, mobile-first cho vùng xa; **sẵn sàng ngôn ngữ dân tộc thiểu số** (mở rộng i18n ngoài "vi mặc định").
- **Vì sao:** R-7 coi công bằng vùng sâu là **yêu cầu lõi, không phải afterthought**. Spec hiện chỉ có WCAG + responsive + i18n-ready chung.
- **Gắn vào đâu:** NFR-21..23 mở rộng; thêm NFR low-bandwidth/offline. Ảnh hưởng FE architecture.
- **Phạm vi:** Tuyên bố NFR + đo lường ở MVP; triển khai offline cache/PWA & gói ngôn ngữ DTTS giai đoạn sau.
- **Công sức/Rủi ro:** TB / Thấp (chủ yếu là NFR + đo, chưa cần làm offline ngay).

### P5 — Kênh giao tiếp & tư vấn chủ động cho Phụ huynh (🟡, khoảng trống R-10)
- **Là gì:** Cho guardian không chỉ "đồng ý + xem hồ sơ" mà còn nhận thông báo tiến bộ, học liệu hướng nghiệp dành cho phụ huynh, kênh liên hệ counselor.
- **Vì sao:** R-10 chỉ rõ "truyền thông/tư vấn cho HS & phụ huynh hạn chế" là khoảng trống thực thi lớn.
- **Gắn vào đâu:** FR nhóm 3.1/3.9; tôn trọng BVDLCN & phạm vi consent (CP-1/4) — chỉ trong quan hệ guardian↔child đã xác minh.
- **Phạm vi:** Giai đoạn sau (sau MVP THCS+THPT lõi).
- **Công sức/Rủi ro:** TB / **TB** (đụng quyền riêng tư — phải qua DPIA cập nhật).

### P6 — Mô hình hệ sinh thái đối tác (trường–ĐH–GDNN–DN) + Program/Event (🟡/⛔)
- **Là gì:** Thực thể hóa đối tác (`Organization`/`Partner`: university, vocational, enterprise) và `Program`/`Event` (workshop, job fair, internship, livestream) để điều phối đa bên.
- **Vì sao:** R-4/R-11. Hiện chỉ có `School` + `Pathway.gdnn`. Đây là tầm "nền tảng quốc gia" thực thụ.
- **Gắn vào đâu:** Data model mới; KHÔNG thuộc lõi pháp lý MVP. Giữ NG-02 (không thành nền tảng tuyển dụng).
- **Phạm vi:** **Roadmap giai đoạn sau** — đề xuất chỉ chốt định hướng + ADR, chưa làm.
- **Công sức/Rủi ro:** Cao / TB (phình phạm vi; cần kiểm soát để không lệch NG-02/NG-03).

### P7 (định vị, không phải tính năng) — Tuyên bố "Cổng hướng nghiệp quốc gia theo TT16"
- **Là gì:** Bổ sung 1 đoạn định vị trong spec §1 nêu rõ WeUp Career đáp ứng vai trò "cổng thông tin hướng nghiệp quốc gia" mà R-2 mô tả, với an toàn TT/BVDLCN đã có.
- **Vì sao:** Tăng tính thuyết phục pháp lý/đối ngoại; chi phí ~0.
- **Phạm vi:** Sửa văn bản spec; MVP.
- **Công sức/Rủi ro:** Rất thấp / Rất thấp.

---

## 4. Ưu tiên & lộ trình đề xuất

| Ưu tiên | Đề xuất | Khi nào | Hình thức áp dụng |
|---|---|---|---|
| **Cao** | P7 định vị cổng quốc gia | MVP (giờ) | Sửa text spec §1 |
| **Cao** | P2 Labor Market Intelligence | MVP | Spec + ADR + dataset tĩnh có nguồn |
| **Cao** | P1 Khung năng lực tư vấn viên | MVP (spec) → Phase 2 (UI) | FR + ADR + data model module độc lập |
| **TB** | P4 Công bằng vùng sâu/offline/DTTS | MVP (NFR) → sau (impl) | Mở rộng NFR + kế hoạch đo |
| **TB** | P3 Làm giàu trải nghiệm nghề | MVP (content type) | Mở rộng `ContentItem.type` |
| **Thấp** | P5 Kênh phụ huynh | Sau MVP | FR + DPIA cập nhật |
| **Thấp** | P6 Hệ sinh thái đối tác + Program/Event | Giai đoạn sau | ADR định hướng, chưa build |

**Nguyên tắc giữ vững khi áp dụng:** cây 12 năng lực ABCD + 2 trục K-A-R/dev_phase là **bất biến**; mọi đề xuất là phân tầng/module thêm, không viết lại lõi (đúng G-07). Mọi bất biến CP-1..CP-8 không bị nới.

---

## 5. ⚠️ Cảnh báo chất lượng nguồn (bắt buộc đọc)

1. **Citations hỏng:** Toàn bộ 72 mục Citations trong báo cáo là `[object Object]` — không truy vết được nguồn gốc. Báo cáo là **tự sinh (GOAP)**, không phải văn bản pháp quy.
2. **Số liệu chưa kiểm chứng** (KHÔNG đưa thẳng vào spec/dataset nếu chưa xác minh):
   - Ngày ký TT 16/2026 = **24/3/2026** → đối chiếu `legal-basis.md` (nguồn có thẩm quyền của dự án) trước khi trích.
   - '19 Train': "gần 500 HS / >30.000 reach"; "80 trainer / 2.700 GV"; ACCA 'Future Pathways' → là minh họa, **không** dùng làm số liệu sản phẩm.
3. **Thẩm quyền:** Khi nghiên cứu ↔ `legal-basis.md` mâu thuẫn, **`legal-basis.md` thắng**. Nghiên cứu chỉ bổ trợ định hướng.
4. **Hệ quả:** P2 (LMI) và bất kỳ dataset nào phải gắn `source_ref` thật + `as_of_date`; tránh "mượn" số liệu chưa kiểm chứng từ báo cáo này.

---

## 6. Câu hỏi cho bạn quyết định

1. Bạn muốn tôi xúc tiến nhóm nào trước? (Khuyến nghị: **P7 + P2 + P1** cho MVP.)
2. P1 (khung năng lực tư vấn viên): mở rộng **spec hiện tại** hay tách **ADR + spec phụ** riêng?
3. P2 (LMI): bạn có **nguồn dữ liệu TTLĐ có thẩm quyền** (HTTT TTLĐ quốc gia / báo cáo ngành) để tôi dựng dataset tĩnh, hay tạm để khung rỗng chờ nguồn?
4. P6 (đối tác/Program-Event): chốt **chỉ định hướng (ADR)** hay đưa vào roadmap có mốc?
5. Có cần tôi soạn **bản cập nhật legal-basis** để xác minh/đính chính ngày & nội dung TT 16/2026 trước, làm nền cho mọi đề xuất?

---

## 7. Ghi chú tuân thủ

- **Chưa thay đổi gì** trong mã nguồn, spec, data model, hay cấu hình. File này thuần đề xuất để bạn xem & đánh giá.
- Khi bạn duyệt từng mục, tôi sẽ làm **doc-first** (spec/ADR trước code) theo đúng quy ước dự án, mỗi mục một slice/PR riêng.
- Mọi đề xuất đụng dữ liệu cá nhân (P5, kênh phụ huynh) sẽ kèm **cập nhật DPIA** trước khi hiện thực.
