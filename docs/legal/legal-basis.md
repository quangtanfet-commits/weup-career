# Căn cứ pháp lý — WeUp Career

> **Tài liệu nền tảng pháp lý** cho nền tảng hướng nghiệp **WeUp Career** (học sinh, sinh viên và người đi làm tại Việt Nam).
> Tài liệu được biên soạn theo chuẩn tắc học thuật: trích dẫn nhất quán, phân loại trạng thái hiệu lực rõ ràng, và truy nguyên nguồn chính thống cho mọi khẳng định pháp lý.

---

## §0. Thông tin tài liệu (Document Control)

### §0.1. Mục đích & phạm vi (Purpose & Scope)

**Mục đích.** Thiết lập nền tảng pháp lý vững chắc, có thể kiểm chứng, làm căn cứ cho (i) *quyết định thiết kế* hệ thống (data model, luồng nghiệp vụ, NFR), (ii) *xác định ranh giới phạm vi* sản phẩm (tránh các nghĩa vụ cấp phép ngoài ý muốn), và (iii) *chứng minh tuân thủ* khi làm việc với cơ quan quản lý, nhà đầu tư, đối tác trường học.

**Phạm vi.** Văn bản quy phạm pháp luật (VBPL) Việt Nam điều chỉnh bốn khối quan hệ mà WeUp Career hoạt động trên giao điểm:

| Khối | Lĩnh vực | Vai trò với sản phẩm |
|---|---|---|
| **A** | Giáo dục hướng nghiệp & phân luồng | *Căn cứ nhu cầu + định hướng nội dung + cơ sở pháp lý trực tiếp* |
| **B** | Việc làm, thị trường lao động & giáo dục nghề nghiệp | *Nguồn dữ liệu nghề + ranh giới "dịch vụ việc làm"* |
| **C** | Bảo vệ dữ liệu cá nhân & trẻ em | *Ràng buộc cứng — quyết định kiến trúc đồng ý & xử lý dữ liệu* |
| **D** | Nền tảng số, dữ liệu, công nghệ số & AI | *Lớp pháp lý của chính loại hình sản phẩm (nền tảng số có lõi AI)* |

**Ngoài phạm vi (loại trừ có chủ đích):** chuẩn nghề nghiệp/mã số–xếp lương/chức danh nhà giáo; chọn sách giáo khoa; quy chế thi & tuyển sinh; chương trình tiếng dân tộc; giáo dục quốc phòng–an ninh; giáo dục mầm non; tư vấn du học; mua sắm CNTT công. Lý do loại trừ từng nhóm: xem §12 và `docs/research/sources.md`.

### §0.2. Phương pháp & nguyên tắc biên soạn (Methodology)

1. **Verify-before-assert.** Mọi *khẳng định pháp lý mới* (số hiệu, ngày ký, ngày hiệu lực, nội dung điều khoản, tình trạng hiệu lực) phải được kiểm chứng qua **nguồn chính thống** (Cổng thông tin Chính phủ `vanban.chinhphu.vn` / `xaydungchinhsach.chinhphu.vn`, Công báo, Hệ thống Văn kiện Đảng) hoặc cơ sở dữ liệu pháp luật uy tín (Thư viện Pháp luật, LuatVietnam) **trước khi** đưa vào tài liệu. Đường dẫn nguồn lưu tại §11.
2. **Phân tầng hệ thống.** VBPL được sắp theo **thứ bậc hiệu lực pháp lý** (Hiến pháp → Luật → Nghị định/Quyết định → Thông tư) và theo **chuỗi cụ thể hóa** (văn bản dưới triển khai văn bản trên). Tham chiếu theo cả chuỗi để bảo đảm căn cứ vững.
3. **Đánh giá trạng thái hiệu lực động.** Mỗi văn bản được gán một *trạng thái hiệu lực tại thời điểm chốt dữ liệu* (xem §0.4). Trạng thái này thay đổi theo thời gian; cần rà soát định kỳ.
4. **Quy ước phân loại theo lĩnh vực ngành.** VBPL của ngành giáo dục (kể cả về CSDL, năng lực số, dạy học trực tuyến) được xếp theo **tầng trong Khối A**, không chuyển sang Khối D. Khối D chỉ chứa VBPL *xuyên ngành* về giao dịch điện tử, dữ liệu, công nghệ số & AI.

> **Ngày chốt dữ liệu (data cutoff): 2026-05-28.** Toàn bộ trạng thái hiệu lực trong tài liệu được tính tại ngày này. Các văn bản có mốc hiệu lực tương lai (vd: TT 33/2026 — hiệu lực 31/5/2026) được đánh dấu *"chưa có hiệu lực"* tương ứng. Số hiệu/ngày/nội dung đã được kiểm chứng qua các vòng tra cứu nguồn chính thống trong các phiên nghiên cứu trước (xem nhật ký §0.5).

### §0.3. Quy ước trích dẫn & bảng chữ viết tắt (Citation Convention & Abbreviations)

**Định dạng trích dẫn chuẩn trong tài liệu:** `[Loại VB] số [số hiệu] ngày [ngày ký] của [cơ quan ban hành]` — ví dụ: *"Thông tư số 16/2026/TT-BGDĐT ngày 24/3/2026 của Bộ GD&ĐT"*. Khi nhắc lại, dùng dạng rút gọn *"TT 16/2026"*. Tham chiếu điều khoản viết tắt *"Đ.5"* (Điều 5), *"k.4"* (khoản 4).

| Viết tắt | Nghĩa | Cấp ban hành |
|---|---|---|
| **NQ** | Nghị quyết | Đảng / Quốc hội |
| **CT** | Chỉ thị | Đảng |
| **QH** | (hậu tố số hiệu Luật) Quốc hội khóa | Quốc hội |
| **Luật** | Luật | Quốc hội |
| **NĐ** (…/NĐ-CP) | Nghị định | Chính phủ |
| **QĐ** (…/QĐ-TTg, …/QĐ-BGDĐT) | Quyết định | Thủ tướng / Bộ trưởng |
| **TT** (…/TT-BGDĐT, …/TT-BLĐTBXH, …/TT-BKHCN) | Thông tư | Bộ |
| **VBHN** (…/VBHN-VPQH) | Văn bản hợp nhất | Văn phòng Quốc hội |
| **BVDLCN** | Bảo vệ dữ liệu cá nhân | — |
| **GDNN** | Giáo dục nghề nghiệp | — |
| **GDĐT / GD&ĐT** | Giáo dục (và Đào tạo) | — |
| **GDPT** | Giáo dục phổ thông | — |
| **GDĐT (Luật 20/2023)** | Giao dịch điện tử | — |
| **HĐTN-HN** | Hoạt động trải nghiệm – Hướng nghiệp | — |
| **TTLĐ / HTTT TTLĐ** | Thị trường lao động / Hệ thống thông tin TTLĐ | — |
| **CSDL / CSDLQG** | Cơ sở dữ liệu / CSDL quốc gia | — |
| **CNCNS** | Công nghiệp công nghệ số | — |
| **DPIA** | Đánh giá tác động xử lý dữ liệu cá nhân | — |

### §0.4. Thang trạng thái hiệu lực (Effectiveness Legend)

Mỗi văn bản được gán một trong sáu trạng thái sau (tính tại ngày chốt **2026-05-28**):

| Ký hiệu | Trạng thái | Ý nghĩa |
|---|---|---|
| ✅ | **Đang có hiệu lực** | Đã phát sinh hiệu lực toàn bộ; áp dụng được ngay. |
| ⏳ | **Đã ban hành, chưa có hiệu lực** | Đã ký/ban hành nhưng ngày hiệu lực ở tương lai; *chưa* viện dẫn làm nghĩa vụ đang áp. |
| 🔄 | **Hiệu lực theo lộ trình / chuyển tiếp** | Phần lớn đã hiệu lực, một số điều khoản hiệu lực sau theo mốc thời gian; hoặc có điều khoản chuyển tiếp. |
| ⚠️ | **Còn hiệu lực nhưng bị sửa đổi / bãi bỏ một phần** | Vẫn áp dụng, song một phần đã bị sửa đổi/thay/bãi bỏ bởi văn bản khác — phải đọc kèm văn bản sửa đổi. |
| ⛔ | **Hết hiệu lực / kết thúc chu kỳ** | Đã bị thay thế hoặc đã hết giai đoạn áp dụng; chỉ dùng *tham chiếu lịch sử*. |
| 📋 | **Văn bản hợp nhất** | Không có hiệu lực độc lập; là bản tra cứu thống nhất nội dung các văn bản đã hợp nhất. |

### §0.5. Nhật ký phiên bản (Changelog)

- **2026-05-28 (v3 — tổ chức lại theo chuẩn học thuật):** Rà soát lại toàn bộ nội dung & **tính hiệu lực** của mọi văn bản; tái cấu trúc tài liệu — bổ sung §0 (thông tin tài liệu: mục đích/phạm vi, phương pháp verify-before-assert + ngày chốt dữ liệu, quy ước trích dẫn + bảng chữ viết tắt, **thang 6 trạng thái hiệu lực**, changelog), §2 (khung phân tích), §3 (**bảng tổng hợp toàn bộ văn bản kèm cột tình trạng**), §8 (**phân tích quan hệ hiệu lực & chuỗi thay thế** — phát hiện chốt: **TT 33/2026 chưa có hiệu lực** đến 31/5/2026). Thêm cột trạng thái hiệu lực vào mọi bảng khối. Đánh số lại toàn bộ mục (§1→§12); cập nhật mọi tham chiếu chéo nội bộ và trong `docs/research/sources.md`, `memory/project-legal-basis.md`. **Không mất thông tin** đã kiểm chứng.
- **2026-05-28 (v2):** Bổ sung 7 VBPL 2024–2026 (TT 16/2026, Luật 123/2025, NQ 71, QĐ 1705…); TT 18/2025 (thay TT 31/2017); Luật GDNN 124/2025 (thay 74/2014); TT 32/2018; **★ lập KHỐI D** (Luật GDĐT 20/2023, Luật Dữ liệu 60/2024, Luật CNCNS 71/2025, **★★ Luật AI 134/2025**, NĐ 69/2024 VNeID); VB chuyển đổi số GD (QĐ 131, TT 02/2025, TT 42/2021); **★★ NĐ 88/2026** (vận hành CSDLQG về GD&ĐT); rà soát 684 VBPL trên moet.gov.vn ⇒ bổ sung 5 TT (33/2026, 04/2014, 30/2023, 22/2021, 18/2026).
- **2026-05-28 (v1):** Bản tổng hợp đầu tiên (Khối A/B/C).

---

## §1. Tóm tắt điều hành (Executive Summary)

WeUp Career hoạt động ở giao điểm của bốn khối pháp luật (§0.1). Ba luận điểm cốt lõi:

1. **Giáo dục hướng nghiệp — sản phẩm được Nhà nước hợp pháp hóa & yêu cầu.** Nhà nước đặt mục tiêu **100% học sinh THCS & THPT được tiếp cận dịch vụ tư vấn hướng nghiệp chuyên nghiệp đến năm 2030** (QĐ 525/QĐ-TTg). Quan trọng hơn, **Thông tư số 16/2026/TT-BGDĐT (Điều 5)** quy định **ứng dụng CNTT & chuyển đổi số trong hướng nghiệp** là **một trong 5 nội dung cốt lõi bắt buộc**. Đây đồng thời là *căn cứ nhu cầu thị trường*, *định hướng nội dung* và *cơ sở pháp lý trực tiếp* cho loại sản phẩm như WeUp Career (phân tích chi tiết: §4.5).

2. **Việc làm & nghề nghiệp — nguồn dữ liệu cho persona người đi làm.** Luật Việc làm 2025 xây dựng Hệ thống thông tin TTLĐ tập trung + Sàn giao dịch việc làm quốc gia, mở khả năng *tích hợp dữ liệu nghề/lương/cung–cầu*. Ranh giới cần giữ: không trở thành "dịch vụ việc làm" cần cấp phép (§5, §9.4).

3. **Bảo vệ dữ liệu cá nhân — ràng buộc cứng quyết định kiến trúc.** Luật BVDLCN 2025 + NĐ 147/2024 đặt nghĩa vụ **nặng** lên nền tảng xử lý dữ liệu, đặc biệt **dữ liệu trẻ em (< 16 tuổi)**; chế tài tới **5% doanh thu**. Cộng với **Luật Trí tuệ nhân tạo 134/2025** (hiệu lực 01/3/2026) điều chỉnh trực tiếp lõi khuyến nghị bằng AI (§7.1), đây là tập ràng buộc *cứng* ảnh hưởng data model, luồng đăng ký, kiến trúc đồng ý và quy trình vận hành.

> **Hệ quả lớn nhất với kiến trúc:** một tỷ lệ đáng kể người dùng học sinh (đặc biệt nhóm phân luồng sau THCS — lớp 9, ~14–15 tuổi) **dưới 16 tuổi**, nên luồng đăng ký & xử lý dữ liệu phải có **cơ chế đồng ý của người đại diện theo pháp luật (cha/mẹ/người giám hộ)** ngay từ MVP, không thể bổ sung sau.

> **Cảnh báo thời điểm (tính đến 2026-05-28):** **TT 33/2026 (Khung năng lực ngoại ngữ) chưa có hiệu lực** — phát sinh hiệu lực **31/5/2026** (còn 3 ngày). Khi mô hình hóa trường `language_level`, dùng văn bản này ở trạng thái "sắp hiệu lực", và lưu ý Khung cũ (01/2014) vẫn dùng tới 31/12/2027 (chuyển tiếp). Các văn bản hiệu lực theo lộ trình khác: §8.

---

## §2. Khung phân tích (Analytical Framework)

Tài liệu phân tích theo hai trục giao nhau.

**Trục 1 — Bốn khối quan hệ pháp luật (A/B/C/D):** đã định nghĩa ở §0.1. Mỗi khối có một mục riêng (§4–§7) với bảng văn bản kèm cột **Tình trạng** hiệu lực.

**Trục 2 — Bốn tầng thứ bậc VBPL** (áp dụng rõ nhất cho Khối A, có mặt ở mọi khối):

```
Tầng 1 — ĐẢNG          (Nghị quyết, Chỉ thị)         → định hướng chính trị
Tầng 2 — QUỐC HỘI      (Luật, Nghị quyết QH)         → luật hóa
Tầng 3 — CHÍNH PHỦ/TTg (Nghị định, Quyết định)       → chiến lược, kế hoạch, quy định chi tiết
Tầng 4 — BỘ            (Thông tư)                    → hướng dẫn chi tiết thi hành
```

Nguyên tắc đọc: **văn bản tầng dưới cụ thể hóa tầng trên**; một căn cứ vững cần dẫn được cả chuỗi (vd: lõi AI của sản phẩm có căn cứ từ NQ 71 của Đảng → Luật 123/2025 Đ.19 + Luật AI 134/2025 của Quốc hội → QĐ 1705/QĐ 131 của Thủ tướng → TT 16/2026 Đ.5đ của Bộ — xem §4.5, §7.1).

Sau bốn khối, **§8 phân tích quan hệ hiệu lực** (chuỗi thay thế, văn bản chưa/sắp hiệu lực, hiệu lực một phần) — phần đặc biệt quan trọng vì nhiều văn bản trụ cột mới hiệu lực giai đoạn 2025–2026.

---

## §3. Bảng tổng hợp văn bản (Master Document Register)

> Bảng tra cứu nhanh **toàn bộ** văn bản trong phạm vi, kèm **trạng thái hiệu lực tại 2026-05-28** (ký hiệu theo §0.4). Chi tiết nội dung & tác động: xem mục khối tương ứng. Văn bản đánh dấu ★ = trụ cột/trung tâm; ★★ = ràng buộc cứng cấp luật.

### Khối A — Giáo dục hướng nghiệp & phân luồng

| Số hiệu | Tên gọi tắt | Cấp | Ngày ký | Hiệu lực | Tình trạng |
|---|---|---|---|---|---|
| 71-NQ/TW | NQ đột phá phát triển GD&ĐT | Đảng | 22/8/2025 | 22/8/2025 | ✅ |
| 29-CT/TW | CT về phân luồng | Đảng | 05/01/2024 | 05/01/2024 | ✅ |
| 43/2019/QH14 | Luật Giáo dục | QH | — | 01/7/2020 | ⚠️ (sửa đổi bởi 123/2025) |
| ★ 123/2025/QH15 | Luật sửa đổi Luật Giáo dục | QH | 10/12/2025 | 01/01/2026 | 🔄 (một số khoản 01/7/2026) |
| 72/VBHN-VPQH | VBHN Luật Giáo dục | QH(VP) | 2026 | — | 📋 |
| QĐ 1705/QĐ-TTg | Chiến lược phát triển GD 2030/2045 | TTg | 31/12/2024 | 31/12/2024 | ✅ |
| ★ QĐ 131/QĐ-TTg | Đề án CNTT & chuyển đổi số GD 2022–2025/2030 | TTg | 25/01/2022 | 25/01/2022 | ✅ (định hướng 2030) |
| ★★ 88/2026/NĐ-CP | NĐ quản lý dữ liệu GD&ĐT (CSDLQG) | CP | 28/3/2026 | 15/5/2026 | ✅ |
| QĐ 525/QĐ-TTg | KH thực hiện CT 29 đến 2030 | TTg | 06/3/2025 | 06/3/2025 | ✅ |
| QĐ 108/QĐ-TTg | KH triển khai Luật 123/2025 | TTg | 16/01/2026 | 16/01/2026 | ✅ |
| 37/2025/NĐ-CP | NĐ chức năng nhiệm vụ Bộ GD&ĐT | CP | 26/2/2025 | 26/2/2025 | ✅ |
| QĐ 522/QĐ-TTg | Đề án hướng nghiệp & phân luồng 2018–2025 | TTg | 14/5/2018 | — | ⛔ (kết thúc chu kỳ) |
| ★ 16/2026/TT-BGDĐT | TT hướng nghiệp & phân luồng | Bộ | — | 24/3/2026 | ✅ |
| 07/2022/TT-BGDĐT | TT tư vấn nghề nghiệp/việc làm/khởi nghiệp | Bộ | — | 08/7/2022 | ✅ |
| 32/2018/TT-BGDĐT | TT Chương trình GDPT 2018 (HĐTN-HN) | Bộ | 26/12/2018 | — | ⚠️ (sửa đổi bởi TT 13/2022, 17/2025…) |
| ★ 18/2025/TT-BGDĐT | TT tư vấn học đường & công tác xã hội | Bộ | 15/9/2025 | 31/10/2025 | ✅ (thay 31/2017+33/2018) |
| 31/2017/TT-BGDĐT | TT tư vấn tâm lý học sinh | Bộ | — | — | ⛔ (bị 18/2025 thay) |
| 20/2023/TT-BGDĐT | TT vị trí việc làm tư vấn học sinh | Bộ | — | 16/12/2023 | ✅ |
| 14/2022/TT-BLĐTBXH | TT hướng nghiệp trong GDNN | Bộ | — | — | ✅ |
| QĐ 1220/QĐ-BGDĐT | KH Bộ GD&ĐT thực hiện QĐ 525 | Bộ | 07/5/2025 | 07/5/2025 | ✅ |
| ★ 02/2025/TT-BGDĐT | TT Khung năng lực số cho người học | Bộ | 24/01/2025 | 11/3/2025 | ✅ |
| 42/2021/TT-BGDĐT | TT CSDL giáo dục & đào tạo (mã định danh) | Bộ | 30/12/2021 | 14/2/2022 | ✅ (thay 26/2019) |
| 09/2021/TT-BGDĐT | TT dạy học trực tuyến (GDPT) | Bộ | 30/3/2021 | 16/5/2021 | ⚠️ (Đ.13 sửa bởi TT 10/2025) |
| 30/2023/TT-BGDĐT | TT đào tạo trực tuyến (GD đại học) | Bộ | 29/12/2023 | 13/2/2024 | ✅ (thay 12/2016) |
| **★ 33/2026/TT-BGDĐT** | **TT Khung năng lực ngoại ngữ** | Bộ | 15/4/2026 | **31/5/2026** | **⏳ chưa có hiệu lực** |
| 22/2021/TT-BGDĐT | TT đánh giá học sinh THCS & THPT | Bộ | 20/7/2021 | 05/9/2021 | ✅ (thay 58/2011+26/2020) |
| ⚠ 04/2014/TT-BGDĐT | TT GD kỹ năng sống & ngoài giờ chính khóa | Bộ | 28/2/2014 | 15/4/2014 | ✅ (ràng buộc cấp phép B2B2C) |
| 18/2026/TT-BGDĐT | TT Khung năng lực số giáo viên | Bộ | 27/3/2026 | 12/5/2026 | ✅ |

### Khối B — Việc làm, TTLĐ & GDNN

| Số hiệu | Tên gọi tắt | Cấp | Ngày ký | Hiệu lực | Tình trạng |
|---|---|---|---|---|---|
| 74/2025/QH15 | Luật Việc làm 2025 | QH | — | 01/01/2026 | ✅ |
| 318/2025/NĐ-CP | NĐ đăng ký lao động & HTTT TTLĐ | CP | — | 01/01/2026 | ✅ |
| 352/2025/NĐ-CP | NĐ giấy phép dịch vụ việc làm | CP | — | 01/01/2026 | ✅ |
| ★ 124/2025/QH15 | Luật Giáo dục nghề nghiệp 2025 | QH | 10/12/2025 | 01/01/2026 | 🔄 (một số điều 01/7/2026) |
| 74/2014/QH13 | Luật Giáo dục nghề nghiệp 2014 | QH | — | — | ⛔ (bị 124/2025 thay) |
| 45/2019/QH14 | Bộ luật Lao động | QH | — | 01/01/2021 | ✅ |

### Khối C — Bảo vệ dữ liệu cá nhân & trẻ em

| Số hiệu | Tên gọi tắt | Cấp | Ngày ký | Hiệu lực | Tình trạng |
|---|---|---|---|---|---|
| ★★ 91/2025/QH15 | Luật BVDLCN 2025 | QH | — | 01/01/2026 | ✅ |
| 356/2025/NĐ-CP | NĐ hướng dẫn Luật BVDLCN | CP | — | 01/01/2026 | ✅ (thay 13/2023) |
| 13/2023/NĐ-CP | NĐ BVDLCN (cũ) | CP | — | 01/7/2023 | ⛔ (bị 356/2025 thay) |
| 147/2024/NĐ-CP | NĐ quản lý Internet & MXH (trẻ <16t) | CP | — | 25/12/2024 | ✅ |
| 24/2018/QH14 | Luật An ninh mạng | QH | — | 01/01/2019 | ✅ |
| 102/2016/QH13 | Luật Trẻ em | QH | — | 01/6/2017 | ✅ |

### Khối D — Nền tảng số, Dữ liệu, Công nghệ số & AI

| Số hiệu | Tên gọi tắt | Cấp | Ngày ký | Hiệu lực | Tình trạng |
|---|---|---|---|---|---|
| 20/2023/QH15 | Luật Giao dịch điện tử | QH | 22/6/2023 | 01/7/2024 | ✅ (thay Luật GDĐT 2005) |
| 194/2025/NĐ-CP | NĐ chi tiết Luật GDĐT (CSDL dùng chung) | CP | 03/7/2025 | 19/8/2025 | ✅ |
| 60/2024/QH15 | Luật Dữ liệu | QH | 30/11/2024 | 01/7/2025 | ✅ |
| ★ 165/2025/NĐ-CP | NĐ chi tiết Luật Dữ liệu | CP | 30/6/2025 | 01/7/2025 | ✅ |
| 71/2025/QH15 | Luật Công nghiệp công nghệ số | QH | 14/6/2025 | 01/01/2026 (Đ.11/28/29: 01/7/2025) | ⚠️ (Chương IV/AI bị 134/2025 bãi bỏ) |
| ★★ 134/2025/QH15 | **Luật Trí tuệ nhân tạo** | QH | 10/12/2025 | 01/3/2026 | ✅ |
| 69/2024/NĐ-CP | NĐ định danh & xác thực điện tử (VNeID) | CP | 25/6/2024 | 01/7/2024 | ✅ (thay 59/2022) |
| QĐ 2439/QĐ-TTg | Khung kiến trúc dữ liệu quốc gia v1.0 | TTg | 04/11/2025 | 04/11/2025 | ✅ |

---

## §4. Khối A — Giáo dục hướng nghiệp & phân luồng

> Hệ thống VBPL giáo dục hướng nghiệp phân tầng 4 cấp (§2 Trục 2): **Đảng định hướng → Quốc hội luật hóa → Chính phủ/Thủ tướng chiến lược → Bộ hướng dẫn chi tiết**. Các bảng dưới dùng định dạng trích dẫn & cột Tình trạng theo §0.3–§0.4.

### §4.1. Tầng 1 — Đảng (định hướng chính trị)

| Văn bản | Số hiệu | Ngày | Tình trạng | Nội dung cốt lõi với WeUp Career |
|---|---|---|---|---|
| **NQ Bộ Chính trị về đột phá phát triển GD&ĐT** | 71-NQ/TW | 22/8/2025 | ✅ | Văn kiện **lịch sử**: định vị đột phá thể chế GD, ngân sách GD **≥ 20% tổng chi**. Một trong 8 đột phá là **chuyển đổi số & ứng dụng AI trong giáo dục** — căn cứ chính trị cao nhất cho nền tảng số hướng nghiệp. "Học đi đôi với hành", học tập suốt đời. |
| **Chỉ thị Bộ Chính trị về phân luồng** | 29-CT/TW | 05/01/2024 | ✅ | Tăng cường phổ cập GD + **đẩy mạnh phân luồng** học sinh sau THCS/THPT đến 2030; khuyến khích ứng dụng **dữ liệu lớn + AI** trong giáo dục. |

### §4.2. Tầng 2 — Quốc hội (luật)

| Văn bản | Số hiệu | Hiệu lực | Tình trạng | Nội dung cốt lõi với WeUp Career |
|---|---|---|---|---|
| **Luật Giáo dục** | 43/2019/QH14 | 01/7/2020 | ⚠️ | Điều 9 định nghĩa **hướng nghiệp** và **phân luồng**; Điều 10 liên thông. *Đọc kèm Luật sửa đổi 123/2025 (đã sửa đổi/bổ sung).* |
| **★ Luật sửa đổi, bổ sung Luật Giáo dục** | 123/2025/QH15 (ký 10/12/2025) | **01/01/2026** (một số khoản 01/7/2026) | 🔄 | **ĐỊNH NGHĨA LẠI phân luồng**: là biện pháp tổ chức GD **trên cơ sở thực hiện hướng nghiệp** (hướng nghiệp là nền, phân luồng là biện pháp xây trên nền đó). Bổ sung trình độ **"trung học nghề"**. Nhấn mạnh năng lực, **sở trường, năng khiếu** cá nhân. **★ Điều 19 (KHCN & đổi mới sáng tạo) = căn cứ TẦNG LUẬT cho lõi số/AI:** k.3 khuyến khích **AI có kiểm soát** trong cơ sở GD; k.4 Nhà nước **đầu tư chuyển đổi số toàn diện** (hạ tầng số, nền tảng số, **CSDL quốc gia về GD&ĐT**); k.5 **ưu tiên phát triển AI trong GD&ĐT**. **Điều 12 (văn bằng)** bổ sung **"bằng trung học nghề"** vào hệ thống văn bằng quốc dân (khớp Luật GDNN 124/2025). Giao Bộ trưởng BGDĐT **quy định chi tiết** ⇒ sinh ra TT 16/2026. Căn cứ Hiến pháp sửa đổi (NQ 203/2025/QH15); kế hoạch thi hành = QĐ 108/QĐ-TTg (16/01/2026). |
| **VBHN Luật Giáo dục** | 72/VBHN-VPQH (2026) | — | 📋 | Bản hợp nhất Luật GD 2019 + sửa đổi 123/2025 — dùng làm bản tra cứu thống nhất, không có hiệu lực độc lập. |

### §4.3. Tầng 3 — Chính phủ / Thủ tướng (chiến lược, kế hoạch, nghị định)

| Văn bản | Số hiệu | Ngày/Hiệu lực | Tình trạng | Nội dung cốt lõi với WeUp Career |
|---|---|---|---|---|
| **Chiến lược phát triển GD đến 2030, tầm nhìn 2045** | QĐ 1705/QĐ-TTg | 31/12/2024 | ✅ | 10 nhiệm vụ; **NV số 8 = đẩy mạnh ứng dụng công nghệ & chuyển đổi số trong giáo dục**. Mục tiêu GD VN đạt trình độ tiên tiến châu Á (2030)/thế giới (2045). |
| **★ Đề án tăng cường ứng dụng CNTT & chuyển đổi số trong GD&ĐT 2022–2025, định hướng 2030** | QĐ 131/QĐ-TTg | 25/01/2022 | ✅ | **Đề án nền cho hệ sinh thái GD số quốc gia.** Lấy **người học/nhà giáo làm trung tâm**; mục tiêu 2025 = 100% người học có **hồ sơ số + mã định danh thống nhất toàn quốc**; 2030 = liên thông CSDL ngành ↔ CSDL quốc gia. **Nêu rõ "tự học với trợ lý ảo"** ⇒ WeUp Career nằm trong định hướng hệ sinh thái GD số; là căn cứ thiết kế **adapter định danh người học** + đồng bộ hồ sơ số. *Mốc 2022–2025 đã qua, song định hướng 2030 vẫn hiệu lực.* |
| **★★ NĐ quản lý dữ liệu giáo dục và đào tạo** | **88/2026/NĐ-CP** | ký 28/3/2026 · **hiệu lực 15/5/2026** | ✅ | **VĂN BẢN VẬN HÀNH CSDL QUỐC GIA VỀ GD&ĐT — cụ thể hóa Luật 123/2025 Đ.19 k.4.** 5 chương 25 điều; căn cứ đồng thời **Luật Dữ liệu 60/2024 + Luật GDĐT 20/2023 + Luật BVDLCN 91/2025 + Luật GD 43/2019 & 123/2025**. Bộ GD&ĐT chủ quản (Đ.14); dữ liệu đặt trên hạ tầng **Trung tâm dữ liệu quốc gia** (Đ.15); CSDLQG là **hệ thống thông tin quan trọng về ANQG**, Bộ Công an thẩm định (Đ.13/19). **Đ.9: mỗi người học có 1 _mã số hồ sơ học tập suốt đời_ theo số định danh cá nhân**; **Đ.12: hồ sơ học tập liên thông tự động trên VNeID**; **Đ.17: kết nối CSDL dân cư/doanh nghiệp/BHXH/y tế**; **Đ.8: lưu trữ hồ sơ học tập vĩnh viễn**; **Đ.4: tổ chức khác dùng dữ liệu GD phải bảo vệ quyền chủ thể theo BVDLCN**. Lộ trình cấp mã số trước **01/01/2027** (Đ.25). ⇒ **Đích & điều kiện pháp lý cho adapter định danh / đồng bộ hồ sơ** (xem §9.1/§9.3/§9.5). |
| **Kế hoạch thực hiện CT 29 đến 2030** | QĐ 525/QĐ-TTg | 06/3/2025 | ✅ | **Chỉ tiêu then chốt: 100% học sinh THCS & THPT được tiếp cận dịch vụ tư vấn hướng nghiệp chuyên nghiệp đến 2030.** Phân luồng phù hợp năng lực/nguyện vọng/hoàn cảnh cá nhân; tạo điều kiện người trong tuổi LĐ tự tạo việc làm/chuyển đổi nghề. |
| **Kế hoạch triển khai Luật 123/2025** | QĐ 108/QĐ-TTg | 16/01/2026 | ✅ | Phân công nhiệm vụ thi hành Luật Giáo dục sửa đổi — bối cảnh triển khai. |
| **NĐ chức năng, nhiệm vụ Bộ GD&ĐT** | 37/2025/NĐ-CP | 26/2/2025 | ✅ | Xác định thẩm quyền Bộ GD&ĐT — cơ sở để Bộ ban hành TT 16/2026. |
| ~~Đề án giáo dục hướng nghiệp & phân luồng~~ | ~~QĐ 522/QĐ-TTg (14/5/2018)~~ | — | ⛔ | **ĐÃ KẾT THÚC chu kỳ 2018–2025.** Tinh thần được kế thừa & thay thế bởi CT 29, QĐ 525, TT 16/2026. Chỉ dùng tham chiếu lịch sử. |

### §4.4. Tầng 4 — Bộ (thông tư hướng dẫn chi tiết)

| Văn bản | Số hiệu | Hiệu lực | Tình trạng | Nội dung cốt lõi với WeUp Career |
|---|---|---|---|---|
| **★ TT hướng nghiệp & phân luồng trong giáo dục** | **16/2026/TT-BGDĐT** | 24/3/2026 | ✅ | **VĂN BẢN TRUNG TÂM, MỚI NHẤT.** 6 chương 21 điều. Cụ thể hóa Luật 123/2025 + NQ 71 + CT 29. **Điều 5 = 5 nội dung cốt lõi** (xem §4.5). Hướng nghiệp **xuyên suốt**; phân luồng **không ép buộc**, dựa năng lực/nguyện vọng. Coi **chuyển đổi số là nội dung bắt buộc**. |
| **TT tư vấn nghề nghiệp, việc làm, khởi nghiệp** | 07/2022/TT-BGDĐT | 08/7/2022 | ✅ | Phân tầng nội dung theo cấp học: Tiểu học = nhận thức; THCS = trải nghiệm; THPT = thực hành/định hướng; ĐH = phát triển nghề nghiệp. |
| **TT ban hành Chương trình GDPT 2018** | 32/2018/TT-BGDĐT | 26/12/2018 | ⚠️ | **Nền chương trình của hướng nghiệp trong trường.** Quy định **Hoạt động trải nghiệm – Hướng nghiệp (HĐTN-HN)** là hoạt động **bắt buộc 105 tiết/năm cả 3 cấp**; 4 mạch nội dung (hướng vào bản thân, hướng đến xã hội, hướng đến tự nhiên, **hướng nghiệp**); 2 giai đoạn (cơ bản: Tiểu học/THCS; định hướng nghề nghiệp: THPT) ⇒ căn cứ ánh xạ nội dung theo `school_level` và điểm tích hợp B2B2C với chương trình chính khóa. *Đã được sửa đổi bởi TT 13/2022, 17/2025, 20/2021 (mang tính housekeeping) — đọc kèm các bản sửa đổi.* |
| **★ TT tư vấn học đường & công tác xã hội trong trường học** | **18/2025/TT-BGDĐT** | 31/10/2025 (ký 15/9/2025) | ✅ | **VĂN BẢN TƯ VẤN HỌC ĐƯỜNG HIỆN HÀNH. Thay thế TT 31/2017 + TT 33/2018.** Áp dụng cả GDPT, GDTX, GDNN, ĐH. Liệt kê **"tư vấn hướng nghiệp và việc làm"** là một nội dung tư vấn (thông tin nghề, xu hướng TTLĐ, kỹ năng chọn nghề, tìm việc, khởi nghiệp, kết nối NSDLĐ). **Nguyên tắc: bảo mật thông tin, tự nguyện, tự quyết định của người học** ⇒ củng cố thiết kế consent Khối C. Có biểu mẫu kế hoạch/chuyển dịch vụ/nhật ký/báo cáo. |
| ~~TT tư vấn tâm lý học sinh trong trường phổ thông~~ | ~~31/2017/TT-BGDĐT~~ | — | ⛔ | **ĐÃ HẾT HIỆU LỰC** (bị TT 18/2025 thay thế từ 31/10/2025). Tinh thần tư vấn tâm lý ↔ hướng nghiệp được kế thừa trong TT 18/2025. Chỉ dùng tham chiếu lịch sử. |
| **TT vị trí việc làm tư vấn học sinh** | 20/2023/TT-BGDĐT | 16/12/2023 | ✅ | Vị trí nhân viên tư vấn học sinh trong trường — đối tác/người dùng tiềm năng (B2B2C). Không bị TT 18/2025 thay thế. |
| **TT công tác hướng nghiệp trong GDNN** | 14/2022/TT-BLĐTBXH | — | ✅ | Hướng nghiệp trong hệ thống giáo dục nghề nghiệp. |
| **KH của Bộ GD&ĐT thực hiện QĐ 525** | QĐ 1220/QĐ-BGDĐT | 07/5/2025 | ✅ | Bộ cụ thể hóa kế hoạch phân luồng/phổ cập của Thủ tướng. |
| **★ TT ban hành Khung năng lực số cho người học** | 02/2025/TT-BGDĐT | 11/3/2025 (ký 24/01/2025) | ✅ | Định nghĩa **năng lực số, an sinh số, nghi thức số, nội dung số**; phụ lục bảng mô tả năng lực thành phần theo bậc (6 miền / 24 năng lực / 4 trình độ / 8 bậc). **Cơ sở chuẩn để WeUp Career thiết kế nội dung & đánh giá năng lực số** — gắn TT 16/2026 Đ.5đ (ứng dụng CNTT/chuyển đổi số). |
| **TT quy định CSDL giáo dục và đào tạo** | 42/2021/TT-BGDĐT | 14/2/2022 (ký 30/12/2021) | ✅ | **Mã định danh GV/HS/SV duy nhất, bất biến, thống nhất xuyên suốt cấp học** (Điều 10); 4 CSDL (mầm non/phổ thông/GDTX/đại học); khai thác qua tài khoản & trục kết nối, chia sẻ dữ liệu. **Đích tích hợp (adapter)** cho định danh người học; tiền đề "CSDL quốc gia về GD&ĐT" (Luật 123/2025 Đ.19 k.4). *Thay thế TT 26/2019.* |
| **TT quản lý & tổ chức dạy học trực tuyến (GDPT)** | 09/2021/TT-BGDĐT | 16/5/2021 (ký 30/3/2021) | ⚠️ | Quy định dạy–học trực tuyến hỗ trợ/thay thế trực tiếp; hạ tầng, học liệu số, trách nhiệm các bên. *Từ 01/7/2025 thẩm quyền tại Điều 13 chuyển về **UBND cấp xã** (TT 10/2025/TT-BGDĐT, do thay đổi mô hình chính quyền địa phương) — đọc kèm.* Tham chiếu khi WeUp Career cung cấp **học liệu/nội dung hướng nghiệp trực tuyến** trong nhà trường (B2B2C). |
| **TT ứng dụng CNTT trong đào tạo trực tuyến (giáo dục ĐẠI HỌC)** | **30/2023/TT-BGDĐT** | 13/2/2024 (ký 29/12/2023) | ✅ | **Thay thế TT 12/2016.** Quy định phần mềm dạy học đồng bộ/không đồng bộ, LMS/LCMS, MOOC cho **giáo dục đại học**; học liệu số phải **thẩm định**; yêu cầu **an toàn thông tin cá nhân + an ninh mạng + sở hữu trí tuệ**; lấy người học làm trung tâm. ⇒ Đồng hành TT 09/2021 (GDPT) cho **phân khúc ĐH/người đi làm**. |
| **★ TT Khung năng lực ngoại ngữ dùng cho Việt Nam** | **33/2026/TT-BGDĐT** | **31/5/2026** (ký 15/4/2026) | **⏳ CHƯA CÓ HIỆU LỰC** (đến 31/5/2026) | **Thay thế Khung 01/2014.** Chuẩn 3 cấp/6 bậc (A1–C2) tham chiếu **CEFR 2020–2021**, **bổ sung bậc Pre-A1**; áp dụng mọi người học ngoại ngữ + "tổ chức, cá nhân có liên quan"; khung cũ dùng tới 31/12/2027 (chuyển tiếp). ⇒ **Chuẩn năng lực ngoại ngữ** để mô hình hóa trường `language_level` (đi kèm TT 02/2025 Khung năng lực số). *Tính đến 2026-05-28: chưa áp dụng — xem §8.1.* |
| **TT đánh giá học sinh THCS & THPT** | **22/2021/TT-BGDĐT** | 05/9/2021 (ký 20/7/2021) | ✅ | **Thay thế TT 58/2011 + 26/2020.** Đánh giá kết quả rèn luyện & học tập theo CT GDPT 2018 (nhận xét + điểm; mức Đạt/Tốt; điều kiện lên lớp). ⇒ **Nguồn dữ liệu hồ sơ học tập** (học lực/năng lực/phẩm chất) để cá nhân hóa gợi ý hướng nghiệp. *(Dữ liệu học tập HS = dữ liệu cá nhân, áp Khối C.)* |
| **⚠ TT quản lý hoạt động GD kỹ năng sống & GD ngoài giờ chính khóa** | **04/2014/TT-BGDĐT** | 15/4/2014 | ✅ (xác minh 2026-05-28) | **RÀNG BUỘC B2B2C TIỀM NĂNG.** Tổ chức/cá nhân tổ chức **hoạt động giáo dục kỹ năng sống** trong nhà trường phải được **cấp phép** (Sở GD&ĐT/hiệu trưởng theo cấp); hồ sơ: tờ trình, kế hoạch, giáo trình; 15 ngày làm việc; thu hồi phép nếu ngừng hoạt động 12 tháng hoặc gian lận. *(TT 29/2024 + 19/2026 về dạy thêm KHÔNG điều chỉnh kỹ năng sống.)* ⇒ Nếu đưa **nội dung kỹ năng vào trường như một hoạt động giáo dục**, phải rà soát ranh giới cấp phép (xem §9.4). |
| **TT Khung năng lực số cho GIÁO VIÊN & cán bộ quản lý** | **18/2026/TT-BGDĐT** | 12/5/2026 (ký 27/3/2026) | ✅ | **Bản song hành phía nhà giáo của TT 02/2025.** 6 miền / 20 năng lực thành phần / 3 mức (cơ bản–thành thạo–nâng cao); **Miền 6 = Ứng dụng AI** (đạo đức, minh bạch, công bằng, bảo vệ dữ liệu cá nhân — đồng hướng Luật AI 134/2025). ⇒ Liên quan **kênh B2B2C cho giáo viên/tư vấn viên**. |

### §4.5. ★ TT 16/2026 Điều 5 — 5 nội dung cốt lõi ↔ tính năng WeUp Career

> Đây là điểm khớp pháp lý quan trọng nhất: **5 nội dung hướng nghiệp bắt buộc** của Thông tư mới ánh xạ gần như **1:1** với bộ tính năng dự kiến của WeUp Career. Mỗi tính năng cốt lõi đều có căn cứ pháp lý trực tiếp.

| TT 16/2026 Điều 5 — Nội dung cốt lõi | Tính năng WeUp Career tương ứng |
|---|---|
| **(a) Cung cấp thông tin nghề nghiệp** — ngành/nghề, yêu cầu năng lực & phẩm chất, điều kiện đào tạo, cơ hội việc làm, xu hướng thị trường lao động | Thư viện ngành/nghề, thông tin trường/ngành, dữ liệu thị trường lao động (liên kết Khối B) |
| **(b) Hỗ trợ học sinh nhận thức bản thân** — khám phá sở trường, năng lực, sở thích | **Trắc nghiệm định hướng** (RIASEC/Holland, MBTI, sở thích/năng lực) — *lưu ý: kết quả = dữ liệu nhạy cảm tiềm năng, xem Khối C* |
| **(c) Phát triển kỹ năng lựa chọn nghề nghiệp** | Lộ trình ra quyết định nghề, công cụ so sánh ngành, nội dung kỹ năng định hướng |
| **(d) Trải nghiệm nghề nghiệp** | Mô phỏng/trải nghiệm nghề, nội dung "một ngày làm nghề", kết nối doanh nghiệp/cơ sở GDNN (giai đoạn sau) |
| **(đ) Ứng dụng CNTT & chuyển đổi số trong hướng nghiệp** | **Chính bản thân nền tảng số WeUp Career** — nội dung này hợp pháp hóa & yêu cầu loại sản phẩm này |

**Phân tích tác động:**
- **Bộ tính năng MVP nên bám sát 5 nội dung Điều 5** để mỗi module có căn cứ pháp lý minh bạch — dùng làm khung phân loại gốc cho `assessment` (b), `content`/`career_info` (a), `guidance`/`pathway` (c), `experience` (d).
- **Mô hình nội dung phân tầng theo cấp học** (Tiểu học → THCS → THPT → ĐH/CĐ → người đi làm) — khớp TT 07/2022; TT 16/2026 yêu cầu nội dung **rà soát/cập nhật định kỳ** & **phù hợp đặc điểm học sinh từng cấp** ⇒ nội dung phải versioned + gắn `school_level`.
- **Phân luồng = biện pháp trên nền hướng nghiệp** (Luật 123/2025): hệ thống nên mô hình hóa hướng nghiệp (assessment + info) làm nền, rồi mới đưa gợi ý phân luồng (học tiếp / trung học nghề / GDNN / lao động) — **không gợi ý phân luồng mang tính ép buộc** (nguyên tắc TT 16/2026).
- **Tệp người dùng B2B2C**: trường học + nhân viên tư vấn học đường (TT 20/2023, TT 18/2025) là kênh phân phối hợp pháp. Cân nhắc vai trò `counselor`/`school_admin`.
- **AI/chuyển đổi số có căn cứ TẦNG LUẬT (Quốc hội), không chỉ dưới luật:** **Luật 123/2025 Điều 19** quy định Nhà nước **đầu tư chuyển đổi số toàn diện** trong GD&ĐT — hạ tầng số, nền tảng số, **CSDL quốc gia về GD&ĐT** (k.4), **ưu tiên đầu tư nghiên cứu/ứng dụng/phát triển AI trong GD&ĐT** (k.5), khuyến khích **AI _có kiểm soát_** trong cơ sở GD (k.3). Phía dưới luật có NQ 71 (Đảng), CT 29 + QĐ 1705 NV8 (Chính phủ), TT 16/2026 Đ.5đ (Bộ) ⇒ một nền pháp lý **4 tầng** cho việc gợi ý ngành/nghề bằng thuật toán/AI. **Ràng buộc thiết kế:** AI phải **"có kiểm soát"** + minh bạch (giải thích được khuyến nghị) + tuân thủ BVDLCN Khối C; để ngỏ **adapter tích hợp CSDL quốc gia về GD&ĐT** (tương tự adapter HTTT TTLĐ ở Khối B). *Chuỗi căn cứ AI đầy đủ 5 tầng sau khi có Luật AI 134/2025: xem §7.1.*

---

## §5. Khối B — Việc làm, thị trường lao động & giáo dục nghề nghiệp

| Văn bản | Số hiệu | Hiệu lực | Tình trạng | Nội dung cốt lõi với WeUp Career |
|---|---|---|---|---|
| **Luật Việc làm 2025** | 74/2025/QH15 | **01/01/2026** | ✅ | Điều 19: Hệ thống thông tin thị trường lao động tập trung, thống nhất toàn quốc, chia sẻ với CSDL quốc gia. Đăng ký lao động cho người **từ 16 tuổi** gắn CSDL dân cư/VNeID. Sàn giao dịch việc làm quốc gia. |
| **NĐ hướng dẫn đăng ký lao động & HTTT TTLĐ** | 318/2025/NĐ-CP | 01/01/2026 | ✅ | Chi tiết nội dung dữ liệu cung–cầu lao động, dự báo TTLĐ trong hệ thống. |
| **NĐ giấy phép dịch vụ việc làm** | 352/2025/NĐ-CP | 01/01/2026 | ✅ | Điều kiện hoạt động **dịch vụ việc làm** — quan trọng nếu WeUp Career có tính năng giới thiệu/kết nối việc làm (xem §9.4). |
| **★ Luật Giáo dục nghề nghiệp** | **124/2025/QH15** (ký 10/12/2025) | **01/01/2026** (một số điều 01/7/2026) | 🔄 | **VĂN BẢN GDNN MỚI NHẤT — thay thế Luật GDNN 74/2014.** Đưa **"trường trung học nghề"** (Điều 9) vào hệ thống giáo dục quốc dân ⇒ cho phép **phân luồng sớm sau THCS** (học văn hóa + học nghề song song). Mạnh phân quyền/phân cấp; bổ sung **Quỹ đào tạo nhân lực doanh nghiệp**. Một trong 4 luật nền (cùng Luật GD, Luật GDĐH, Luật Nhà giáo). Ký bởi CT Quốc hội Trần Thanh Mẫn. |
| ~~Luật Giáo dục nghề nghiệp~~ | ~~74/2014/QH13~~ | — | ⛔ | **ĐÃ HẾT HIỆU LỰC** (bị 124/2025 thay thế từ 01/01/2026). Chính sách phân luồng HS tốt nghiệp THCS/THPT vào GDNN; các trình độ sơ cấp/trung cấp/cao đẳng; liên thông. Chỉ dùng tham chiếu lịch sử. |
| **Bộ luật Lao động** | 45/2019/QH14 | 01/01/2021 | ✅ | Khung quan hệ lao động; độ tuổi lao động; lao động chưa thành niên — nền cho nội dung "thế giới nghề nghiệp" của persona người đi làm. |

**Phân tích tác động:**
- **Persona người đi làm** có thể được hỗ trợ bằng dữ liệu nghề/kỹ năng/cung-cầu lấy từ HTTT thị trường lao động quốc gia (Điều 19 Luật 74/2025). Thiết kế nên để ngỏ **cổng tích hợp (adapter)** đọc dữ liệu TTLĐ, dù MVP có thể dùng dataset tĩnh.
- **Mốc 16 tuổi** trong đăng ký lao động trùng với mốc 16 tuổi của NĐ 147/2024 (mạng xã hội) và mốc trẻ em — củng cố lựa chọn lấy **16 tuổi làm ngưỡng phân luồng người dùng** trong hệ thống.
- **Cảnh báo pháp lý:** nếu thêm tính năng *giới thiệu việc làm/tuyển dụng*, có thể rơi vào phạm vi "dịch vụ việc làm" cần giấy phép (NĐ 352/2025). MVP nên giới hạn ở **thông tin & định hướng**, chưa làm trung gian tuyển dụng, để tránh nghĩa vụ cấp phép (§9.4).
- **Khung phân luồng GDNN** (Luật GDNN **124/2025**) bổ sung trục dữ liệu: ngành nghề ↔ trình độ đào tạo (sơ cấp/trung cấp/cao đẳng) ↔ cơ sở GDNN. **Loại cơ sở mới "trường trung học nghề"** (Đ.9) cần được mô hình hóa như một nhánh phân luồng sau THCS — bổ sung vào enum `school_type`/`pathway`.

---

## §6. Khối C — Bảo vệ dữ liệu cá nhân & trẻ em (RÀNG BUỘC CỨNG)

| Văn bản | Số hiệu | Hiệu lực | Tình trạng |
|---|---|---|---|
| **Luật Bảo vệ dữ liệu cá nhân 2025** | 91/2025/QH15 | **01/01/2026** | ✅ — văn bản trụ cột |
| **NĐ hướng dẫn Luật BVDLCN** | 356/2025/NĐ-CP | 01/01/2026 | ✅ — thay thế NĐ 13/2023 |
| ~~Nghị định BVDLCN~~ | ~~13/2023/NĐ-CP~~ | ~~01/7/2023~~ | ⛔ — bị 356/2025 thay thế |
| **NĐ quản lý Internet & mạng xã hội** | 147/2024/NĐ-CP | 25/12/2024 | ✅ — quy định trẻ < 16 tuổi |
| **Luật An ninh mạng** | 24/2018/QH14 | 01/01/2019 | ✅ — Điều 29 bảo vệ trẻ em trên không gian mạng |
| **Luật Trẻ em** | 102/2016/QH13 | 01/6/2017 | ✅ — Điều 54 bảo vệ trẻ em trên môi trường mạng |

**Quy định then chốt phải tuân thủ:**

1. **Phân loại dữ liệu cơ bản vs nhạy cảm** (Luật 91/2025). Dữ liệu nhạy cảm gồm: quan điểm chính trị/tôn giáo, sức khỏe, đời sống riêng tư, sinh trắc học/di truyền, định vị, lịch sử tội phạm, tài khoản tài chính. → **Kết quả trắc nghiệm tính cách/định hướng (MBTI, RIASEC) có thể chạm tới đời sống riêng tư** ⇒ xử lý ở mức bảo vệ cao.
2. **Đồng ý phải chủ động** (opt-in): im lặng/không phản hồi **không** phải đồng ý; ô tick sẵn (pre-ticked) **vô hiệu**. Phải cho **rút lại đồng ý bất kỳ lúc nào** và dừng xử lý ngay.
3. **Dữ liệu trẻ em** (Luật 91/2025 + NĐ 356/2025):
   - Phải có **sự đồng ý của người đại diện theo pháp luật** (cha/mẹ/người giám hộ).
   - Trẻ **từ đủ 7 tuổi trở lên**: việc công bố/tiết lộ đời sống riêng tư cần đồng ý của **cả trẻ em và người đại diện**.
   - Nguyên tắc: vì **lợi ích tốt nhất của trẻ em**.
4. **NĐ 147/2024 — trẻ < 16 tuổi**: **không được tự đăng ký tài khoản**; cha/mẹ/người giám hộ đăng ký bằng thông tin của mình và giám sát hoạt động. Áp dụng cả nền tảng trong nước & xuyên biên giới.
5. **Chế tài**: phạt tới **5% tổng doanh thu**. Cơ quan đầu mối: **A05 — Bộ Công an**. Có **Cổng thông tin quốc gia về BVDLCN** để đăng ký/báo cáo.
6. **Đánh giá tác động (DPIA)**: doanh nghiệp nhỏ/khởi nghiệp được hoãn tối đa 5 năm — **TRỪ** khi xử lý dữ liệu nhạy cảm hoặc số lượng lớn chủ thể. → WeUp Career xử lý dữ liệu trẻ em + có thể là dữ liệu nhạy cảm ⇒ **khả năng cao phải làm DPIA ngay**, không được hoãn.
7. **Chuyển dữ liệu ra nước ngoài**: phải đánh giá tác động trong 60 ngày kể từ khi bắt đầu chuyển. → Ảnh hưởng lựa chọn nhà cung cấp hosting/AI nước ngoài.

---

## §7. Khối D — Nền tảng số, Dữ liệu, Công nghệ số & Trí tuệ nhân tạo (LỚP PHÁP LÝ SẢN PHẨM)

> Đây là **lớp pháp lý của chính loại sản phẩm** WeUp Career (một nền tảng số có lõi AI xử lý dữ liệu). Khác với Khối A/B/C (điều chỉnh *nội dung* hướng nghiệp, việc làm, dữ liệu cá nhân), Khối D điều chỉnh **hình thức kỹ thuật** của sản phẩm: giao dịch điện tử, hạ tầng dữ liệu quốc gia, công nghệ số và **trí tuệ nhân tạo**. Giai đoạn 2024–2026 Việt Nam vừa luật hóa toàn bộ lớp này ⇒ thiết kế phải tuân thủ ngay, đặc biệt **Luật Trí tuệ nhân tạo 134/2025** (hiệu lực 01/3/2026).

| Văn bản | Số hiệu | Hiệu lực | Tình trạng | Nội dung cốt lõi với WeUp Career |
|---|---|---|---|---|
| **Luật Giao dịch điện tử** | 20/2023/QH15 | 01/7/2024 | ✅ (thay Luật GDĐT 2005) | Giá trị pháp lý của **thông điệp dữ liệu, chữ ký điện tử/số, hợp đồng điện tử, chứng thư điện tử**; bản điện tử ↔ bản giấy có giá trị tương đương khi đủ điều kiện; **dịch vụ tin cậy** do Bộ KH&CN/TT&TT quản lý. ⇒ Căn cứ để **e-consent (ConsentRecord) & chữ ký điện tử của người giám hộ** có giá trị pháp lý. |
| ↳ NĐ chi tiết Luật GDĐT (CSDL & nền tảng số dùng chung QG) | 194/2025/NĐ-CP (03/7/2025) | 19/8/2025 | ✅ | Hướng dẫn thi hành **Luật GDĐT 20/2023** về **cơ sở dữ liệu dùng chung, kết nối/chia sẻ dữ liệu, dữ liệu mở** và **Khung kiến trúc tổng thể quốc gia số**. Chủ yếu điều chỉnh hoạt động của **cơ quan nhà nước**. ⇒ **Tham chiếu kỹ thuật** (chuẩn kết nối, định dạng chia sẻ, dữ liệu mở) cho adapter — *không ràng buộc trực tiếp* nền tảng tư nhân. |
| **Luật Dữ liệu** | 60/2024/QH15 | 01/7/2025 | ✅ | Lập **Trung tâm dữ liệu quốc gia** (Bộ Công an), **CSDL tổng hợp quốc gia**; quy định **dữ liệu là tài nguyên/tài sản**, quản trị dữ liệu, **chuyển dữ liệu xuyên biên giới**, sản phẩm/dịch vụ dữ liệu. *Khác Luật BVDLCN 91/2025 (Khối C — bảo vệ dữ liệu cá nhân).* ⇒ Quy tắc hạ tầng & xuyên biên giới khi tích hợp CSDLQG / lưu trữ dữ liệu lớn. |
| ↳ ★ NĐ chi tiết một số điều Luật Dữ liệu | 165/2025/NĐ-CP (30/6/2025) | 01/7/2025 | ✅ | Hướng dẫn thi hành **Luật Dữ liệu 60/2024**; **áp dụng RỘNG cho cả tổ chức/cá nhân Việt Nam & nước ngoài** có hoạt động dữ liệu tại VN. Quy định **quản lý rủi ro dữ liệu, tiêu chí dữ liệu quan trọng/cốt lõi, đánh giá rủi ro ĐỊNH KỲ HẰNG NĂM, lưu trữ dữ liệu**. *Khác NĐ 356/2025 (thi hành Luật BVDLCN 91/2025 — Khối C).* ⇒ **CÓ THỂ ÁP cho WeUp Career**: phân loại dữ liệu, quy trình quản trị & **đánh giá rủi ro dữ liệu hằng năm**. |
| **Luật Công nghiệp công nghệ số** | 71/2025/QH15 | 01/01/2026 (Đ.11/28/29 từ 01/7/2025) | ⚠️ | Khung công nghiệp công nghệ số, bán dẫn, **tài sản số**, ưu đãi doanh nghiệp công nghệ số. **⚠ Chương IV (AI) của luật này đã bị Luật AI 134/2025 Đ.33 BÃI BỎ — không viện dẫn Chương IV làm căn cứ AI sống.** ⇒ Dùng cho định vị ngành/ưu đãi, không dùng cho nghĩa vụ AI (xem §8.4). |
| **★★ Luật Trí tuệ nhân tạo** | **134/2025/QH15** (ký 10/12/2025) | **01/3/2026** | ✅ | **LUẬT AI ĐẦU TIÊN CỦA VIỆT NAM — RÀNG BUỘC CỨNG cho lõi khuyến nghị của WeUp Career.** 8 chương 35 điều. Nguyên tắc: **lấy con người làm trung tâm; AI phục vụ con người, KHÔNG thay thế thẩm quyền/trách nhiệm con người**; công bằng, minh bạch, không thiên lệch/phân biệt đối xử; trách nhiệm giải trình. **Phân loại rủi ro** cao/trung bình/thấp; **tự phân loại + thông báo Bộ KH&CN** qua cổng một cửa AI. Hệ thống **rủi ro cao** phải: đánh giá sự phù hợp + hồ sơ kỹ thuật + nhật ký vận hành + **bảo đảm con người giám sát/can thiệp được**; **gắn nhãn nội dung do AI tạo** (deepfake). Phân định trách nhiệm nhà phát triển/cung cấp/triển khai/người dùng. KHÔNG bắt tiết lộ mã nguồn/thuật toán. Cơ quan: **Bộ KH&CN**. (Chi tiết nghĩa vụ ↔ thiết kế: §7.1.) |
| **NĐ định danh & xác thực điện tử (VNeID)** | 69/2024/NĐ-CP (25/6/2024) | 01/7/2024 | ✅ (thay NĐ 59/2022) | 6 chương 41 điều. Tài khoản định danh điện tử **VNeID** (Cục C06 Bộ Công an) **có giá trị chứng minh tương đương giấy tờ**. **Trẻ được cấp tài khoản RIÊNG** (khác NĐ 59/2022 gộp theo tài khoản cha mẹ): **6–<14 = mức 01 (mức 02 khi có nhu cầu)**; **<6 = mức 01 khi có nhu cầu**; **≥14 = mức 01/02**. ⇒ Cơ hội dùng VNeID để **xác thực giám hộ & độ tuổi**, tăng độ tin cậy luồng đăng ký < 16t (Khối C). *Lưu ý: mốc tuổi VNeID (6/14) KHÁC mốc đồng ý/đăng ký <16t (NĐ 147/2024) — đủ điều kiện có VNeID ≠ đủ năng lực tự đồng ý.* |
| ↳ Khung kiến trúc dữ liệu quốc gia | QĐ 2439/QĐ-TTg (04/11/2025) | 04/11/2025 | ✅ | Khung kiến trúc dữ liệu QG + Khung quản trị/quản lý dữ liệu QG + Từ điển dữ liệu dùng chung v1.0. Áp cho hệ thống chính trị/cơ quan nhà nước; nguyên tắc "lưu trữ tối thiểu / thu thập một lần / chia sẻ minh bạch" — **tham chiếu chuẩn dữ liệu** cho adapter CSDLQG, không ràng buộc trực tiếp. |

### §7.1. ★★ Luật AI 134/2025 — nghĩa vụ ↔ thiết kế WeUp Career (HARD constraint)

> Lõi giá trị của WeUp Career là **gợi ý ngành/nghề/lộ trình bằng thuật toán/AI** dựa trên trắc nghiệm (RIASEC/MBTI) + hồ sơ người dùng. Đây gần như chắc chắn là một **hệ thống AI thuộc phạm vi Luật 134/2025**, và do **tác động tới giáo dục/định hướng tương lai của trẻ vị thành niên** nên **khả năng cao bị xếp rủi ro TRUNG BÌNH→CAO**. Mọi nghĩa vụ dưới đây phải trở thành **NFR bắt buộc** trong `docs/spec.md`.

| Nghĩa vụ Luật AI 134/2025 | Hệ quả thiết kế WeUp Career |
|---|---|
| **Con người làm trung tâm — AI không thay thế quyết định của con người** (Đ.4) | **Human-in-the-loop**: hệ thống chỉ **gợi ý**, không tự động ra quyết định phân luồng/chọn nghề ⇒ trùng khớp & củng cố nguyên tắc "**không ép buộc phân luồng**" (TT 16/2026, Luật 123/2025). Luôn có "đề xuất + lý do + người dùng/giáo viên/giám hộ quyết định". |
| **Tự phân loại rủi ro + thông báo Bộ KH&CN** (Đ.9–10) | Quy trình tuân thủ: **đánh giá & ghi nhận mức rủi ro** của engine khuyến nghị; nếu rủi ro cao → **thông báo qua cổng một cửa AI** + làm **đánh giá sự phù hợp** (Đ.13). Đưa vào checklist go-live. |
| **Minh bạch & giải trình** (Đ.11) | **Explainable recommendation**: mỗi gợi ý kèm **lý do** (yếu tố đầu vào, trọng số định tính), mô tả mục đích/nguyên lý/nguồn dữ liệu của mô hình; **KHÔNG cần lộ mã nguồn/tham số**. Hiển thị **"khuyến nghị được hỗ trợ bởi AI"** (AI-disclosure). |
| **Không thiên lệch / không phân biệt đối xử** (Đ.4) | **Bias testing** bộ trắc nghiệm & thuật toán theo giới tính/vùng miền/hoàn cảnh; kiểm thử công bằng định kỳ; tài liệu hóa kết quả. Trắc nghiệm RIASEC/MBTI không được khóa cứng lựa chọn theo định kiến. |
| **Nhật ký vận hành + hồ sơ kỹ thuật** (Đ.11, rủi ro cao) | **Audit log** quyết định/gợi ý của AI (đã có yêu cầu audit ở Khối C) + **model card/hồ sơ kỹ thuật** (mục đích, dữ liệu huấn luyện, giới hạn, kiểm soát rủi ro) lưu trữ phục vụ thanh tra. |
| **Gắn nhãn nội dung do AI tạo** (Đ.11) | Nếu sinh nội dung tư vấn/bài viết/hình ảnh bằng AI ⇒ **gắn nhãn AI-generated**. |
| **Phân định trách nhiệm các bên** (nhà phát triển/cung cấp/triển khai) | Hợp đồng & điều khoản phải **phân vai trò pháp lý** (ai là provider, ai là deployer); không "đổ lỗi cho thuật toán" khi có sai sót khuyến nghị. |

**Liên kết tầng pháp lý cho AI (nay 5 tầng, đầy đủ nhất):** Đảng (NQ 71) → **Quốc hội: Luật 123/2025 Đ.19 "AI có kiểm soát" + ★★ Luật AI 134/2025 (luật chuyên ngành)** → Chính phủ/Thủ tướng (QĐ 1705 NV8, QĐ 131) → Bộ (TT 16/2026 Đ.5đ, TT 02/2025 Khung năng lực số). Trước đây AI chỉ có nền định hướng + một điều khoản trong luật GD; **nay có luật chuyên ngành riêng với nghĩa vụ cụ thể** ⇒ tuân thủ là điều kiện tồn tại của sản phẩm, không phải tùy chọn.

---

## §8. Phân tích quan hệ hiệu lực & chuỗi thay thế (Supersession & Effectiveness Analysis)

> Mục này tổng hợp **động học hiệu lực** của hệ thống VBPL: văn bản nào *chưa/sắp* có hiệu lực, văn bản nào *thay thế* văn bản nào, và những phần *bị bãi bỏ một phần*. Đặc biệt quan trọng vì nhiều văn bản trụ cột mới hiệu lực 2025–2026 — đọc sai mốc có thể dẫn tới viện dẫn văn bản chưa hiệu lực hoặc đã chết.

### §8.1. ⏳ Văn bản đã ban hành nhưng CHƯA có hiệu lực (tính đến 2026-05-28)

| Văn bản | Hiệu lực | Khoảng cách | Xử lý |
|---|---|---|---|
| **TT 33/2026/TT-BGDĐT** (Khung năng lực ngoại ngữ) | **31/5/2026** | **còn 3 ngày** | **Chưa áp dụng.** Khi mô hình hóa `language_level`, dùng như chuẩn "sắp hiệu lực". Khung cũ 01/2014 **vẫn dùng tới 31/12/2027** (điều khoản chuyển tiếp) ⇒ giai đoạn 31/5/2026–31/12/2027 hai khung **song song**. Theo dõi mốc 31/5/2026. |

> *Đây là phát hiện chốt của vòng rà soát hiệu lực:* TT 33/2026 đã ký (15/4/2026) và nằm trong tài liệu, nhưng **chưa phát sinh hiệu lực** tại ngày chốt. Không được trình bày nghĩa vụ của nó như đang áp.

### §8.2. 🔄 Văn bản hiệu lực theo lộ trình / có điều khoản chuyển tiếp

| Văn bản | Mốc hiệu lực | Ghi chú lộ trình |
|---|---|---|
| **Luật 123/2025/QH15** (sửa đổi Luật GD) | 01/01/2026; **một số khoản 01/7/2026** | Phần lớn đã hiệu lực; rà soát các khoản lùi tới 01/7/2026 trước khi viện dẫn chi tiết. *Điều khoản chuyển tiếp Đ.34: bằng tốt nghiệp THCS cấp trước 01/01/2026 vẫn có giá trị — lưu ý khi mô hình hóa văn bằng.* |
| **Luật GDNN 124/2025/QH15** | 01/01/2026; **một số điều 01/7/2026** | Tương tự — phân quyền/mô hình "trường trung học nghề" cần kiểm tra mốc khoản cụ thể. |
| **Luật CNCNS 71/2025/QH15** | 01/01/2026; **Đ.11/28/29 từ 01/7/2025** | Một số điều hiệu lực sớm (01/7/2025); xem thêm §8.4 (Chương IV/AI đã bị bãi bỏ). |
| **TT 33/2026** (khung ngoại ngữ) | 31/5/2026; **khung cũ 01/2014 dùng tới 31/12/2027** | Đã nêu §8.1 — giai đoạn chuyển tiếp hai khung song song. |
| **NĐ 88/2026/NĐ-CP** | hiệu lực 15/5/2026; **cấp mã số hồ sơ học tập suốt đời trước 01/01/2027** (Đ.25) | Văn bản đã hiệu lực, song *cơ chế cấp mã số* triển khai dần tới 01/01/2027 — adapter định danh chỉ khả thi sau khi cơ chế vận hành. |

### §8.3. ⛔ Văn bản hết hiệu lực / kết thúc chu kỳ (chuỗi thay thế)

| Văn bản cũ (⛔) | Bị thay bởi | Mốc | Khối |
|---|---|---|---|
| QĐ 522/QĐ-TTg (Đề án hướng nghiệp 2018–2025) | *Kết thúc chu kỳ* — kế thừa tinh thần bởi CT 29 + QĐ 525 + TT 16/2026 | hết 2025 | A |
| TT 31/2017 + TT 33/2018 (tư vấn tâm lý/CTXH học đường) | **TT 18/2025/TT-BGDĐT** | 31/10/2025 | A |
| TT 26/2019 (CSDL GD) | **TT 42/2021/TT-BGDĐT** | 14/2/2022 | A |
| TT 12/2016 (đào tạo trực tuyến ĐH) | **TT 30/2023/TT-BGDĐT** | 13/2/2024 | A |
| TT 58/2011 + TT 26/2020 (đánh giá HS) | **TT 22/2021/TT-BGDĐT** | 05/9/2021 | A |
| Khung năng lực ngoại ngữ 01/2014 | **TT 33/2026** (⏳ từ 31/5/2026; cũ dùng tới 31/12/2027) | chuyển tiếp | A |
| Luật GDNN 74/2014/QH13 | **Luật GDNN 124/2025/QH15** | 01/01/2026 | B |
| NĐ 13/2023/NĐ-CP (BVDLCN) | **NĐ 356/2025/NĐ-CP** | 01/01/2026 | C |
| NĐ 59/2022 (định danh điện tử) | **NĐ 69/2024/NĐ-CP** | 01/7/2024 | D |
| Luật Giao dịch điện tử 2005 | **Luật GDĐT 20/2023/QH15** | 01/7/2024 | D |

### §8.4. ⚠️ Văn bản còn hiệu lực nhưng bị sửa đổi / bãi bỏ một phần

| Văn bản | Phần bị tác động | Bởi văn bản | Hệ quả |
|---|---|---|---|
| **Luật CNCNS 71/2025** | **Chương IV (Trí tuệ nhân tạo) — BÃI BỎ** | Luật AI 134/2025 **Đ.33** | **Không viện dẫn Ch IV làm căn cứ AI.** Phần tài sản số / bán dẫn / cơ chế thử nghiệm có kiểm soát **vẫn hiệu lực** — chỉ dùng cho định vị ngành/ưu đãi. |
| **Luật Giáo dục 43/2019** | Nhiều điều **sửa đổi, bổ sung** | Luật 123/2025 | Đọc kèm bản sửa đổi; ưu tiên VBHN 72/VBHN-VPQH để tra cứu thống nhất. |
| **TT 09/2021** (dạy học trực tuyến GDPT) | **Điều 13** (thẩm quyền) chuyển về UBND cấp xã từ 01/7/2025 | TT 10/2025/TT-BGDĐT | Khi tham chiếu thẩm quyền tổ chức dạy học trực tuyến, dùng quy định mới. |
| **TT 32/2018** (CT GDPT 2018) | Một số nội dung chương trình sửa đổi (housekeeping) | TT 13/2022, 17/2025, 20/2021 | Cốt lõi HĐTN-HN giữ nguyên; đọc kèm các bản sửa đổi khi cần chi tiết chương trình. |

### §8.5. Tổng kết kiểm tra hiệu lực

- **Số văn bản trong phạm vi:** ~48 (Khối A 27 · B 6 · C 6 · D 8, có giao thoa tham chiếu).
- **Đang có hiệu lực ✅:** đa số văn bản trụ cột (Luật BVDLCN 91/2025, Luật AI 134/2025, TT 16/2026, NĐ 88/2026, Luật Việc làm 74/2025…).
- **Cần theo dõi mốc tương lai:** **TT 33/2026 (⏳ 31/5/2026)**; các khoản lùi 01/7/2026 của Luật 123/2025 & 124/2025; cơ chế cấp mã số NĐ 88/2026 (tới 01/01/2027).
- **Không được viện dẫn:** QĐ 522, TT 31/2017, Luật GDNN 74/2014, NĐ 13/2023, **Chương IV Luật CNCNS 71/2025** (chỉ tham chiếu lịch sử/định vị).
- **Khuyến nghị rà soát:** đặt lịch kiểm tra lại trạng thái hiệu lực **mỗi quý** hoặc khi có VBPL mới; cập nhật cột Tình trạng §3 + changelog §0.5.

---

## §9. Tác động lên thiết kế hệ thống (Design Impact)

### §9.1. Mô hình dữ liệu (Data model)
- **`User` cần `date_of_birth` (hoặc `age_band`) + `user_type`** (`student` / `working`) làm trục phân luồng pháp lý.
- **Quan hệ giám hộ**: `Guardian` ↔ `MinorAccount` cho người dùng < 16 tuổi (NĐ 147/2024). Tài khoản trẻ em **liên kết tài khoản người giám hộ**.
- **`ConsentRecord`** (chủ thể, loại dữ liệu, mục đích, thời điểm, kênh, trạng thái rút lại) — bắt buộc để chứng minh đồng ý chủ động & hỗ trợ rút lại. Để ngỏ trường **`signature_type`/`signature_ref`** cho chữ ký điện tử của giám hộ (Luật GDĐT 20/2023).
- **Đánh dấu trường nhạy cảm**: kết quả trắc nghiệm định hướng/tính cách phải gắn cờ "nhạy cảm" → mã hóa, kiểm soát truy cập chặt hơn, audit log.
- **Trục phân loại nội dung theo cấp học** (TT 07/2022): Tiểu học/THCS/THPT/ĐH-CĐ/người đi làm.
- **`AIRecommendation` / nhật ký AI** (Luật AI 134/2025): mỗi gợi ý lưu **đầu vào, mô hình/phiên bản, lý do giải trình, người duyệt (nếu có), thời điểm** — phục vụ minh bạch + nhật ký vận hành + audit.
- **Định danh người học**: để ngỏ trường `national_edu_id` (mã định danh ngành GD — TT 42/2021), `lifelong_learning_id` (**mã số hồ sơ học tập suốt đời** theo số định danh cá nhân — NĐ 88/2026 Đ.9) và `vneid_verified` (NĐ 69/2024) cho adapter định danh/đồng bộ hồ sơ số (không bắt buộc ở MVP). Kết nối CSDLQG về GD&ĐT chỉ thực hiện theo cơ chế chia sẻ có kiểm soát (NĐ 88/2026 Đ.17), không tự ý đồng bộ.

### §9.2. Luồng đăng ký (Registration flow)
- Bắt buộc **kiểm tra độ tuổi** ngay bước đầu.
- **< 16 tuổi** ⇒ luồng đăng ký qua người giám hộ (thông tin & xác nhận của cha/mẹ/người giám hộ), không cho tự tạo tài khoản độc lập.
- **Đồng ý xử lý dữ liệu** dạng opt-in rõ ràng, tách bạch theo mục đích; không pre-tick; lưu `ConsentRecord`. Đồng ý/điều khoản dạng điện tử có **giá trị pháp lý** theo Luật GDĐT 20/2023.
- Cung cấp **trang quản lý đồng ý & rút lại đồng ý** trong hồ sơ người dùng.
- **Tùy chọn xác thực mạnh qua VNeID** (NĐ 69/2024) để xác nhận quan hệ giám hộ & độ tuổi thật — giảm rủi ro khai man tuổi; cân nhắc cho giai đoạn sau MVP.

### §9.3. Tuân thủ & vận hành (Compliance & Ops)
- **DPIA** từ đầu (xử lý dữ liệu trẻ em + dữ liệu nhạy cảm — không được hoãn).
- Ưu tiên **lưu trữ dữ liệu trong nước**; nếu dùng dịch vụ nước ngoài (AI, hosting) phải đánh giá tác động chuyển dữ liệu xuyên biên giới (60 ngày — Luật BVDLCN 91/2025; quy tắc hạ tầng/dữ liệu xuyên biên giới — Luật Dữ liệu 60/2024).
- **Audit log** cho mọi truy cập dữ liệu nhạy cảm/trẻ em **và mọi gợi ý của AI** (đã khớp với ràng buộc bảo mật hiện có: no PII in logs, IDOR protection, 404-not-403; bổ sung nhật ký AI theo Luật 134/2025).
- Chuẩn bị quy trình **tiếp nhận yêu cầu chủ thể dữ liệu** (truy cập, sửa, xóa, rút đồng ý).
- **Ranh giới lưu trữ vĩnh viễn (NĐ 88/2026 Đ.8) ≠ áp cho WeUp Career.** Nghĩa vụ "lưu trữ hồ sơ học tập vĩnh viễn" gắn với **CSDL quốc gia về GD&ĐT** (hệ thống của Nhà nước, Bộ GD&ĐT chủ quản). WeUp Career là **"tổ chức khác" (NĐ 88/2026 Đ.4)** ⇒ chỉ được xử lý dữ liệu GD trong phạm vi chức năng, **bảo vệ quyền chủ thể theo Luật BVDLCN 91/2025** (tối thiểu hóa, quyền xóa, thời hạn lưu theo mục đích) — **không** tự áp đặt lưu vĩnh viễn cho dữ liệu người dùng của nền tảng.

### §9.4. Phạm vi tính năng MVP (Scope guardrails)
- ✅ Trong phạm vi: hồ sơ hướng nghiệp, trắc nghiệm định hướng, tư vấn ngành/trường (thông tin), lộ trình kỹ năng.
- ⚠️ Cần cân nhắc cấp phép: **trung gian giới thiệu/tuyển dụng việc làm** (NĐ 352/2025) → **để giai đoạn sau**, MVP chỉ cung cấp thông tin & định hướng.
- ⚠️ Cần cân nhắc cấp phép: **hoạt động giáo dục kỹ năng sống trong nhà trường** (TT 04/2014/TT-BGDĐT) → nếu triển khai nội dung kỹ năng/chọn nghề **dưới dạng một hoạt động giáo dục tổ chức trong trường** (B2B2C), phải rà soát nghĩa vụ cấp phép Sở GD&ĐT. MVP số thuần (cung cấp thông tin/công cụ trực tuyến) rủi ro thấp; **không** đóng gói thành "chương trình kỹ năng sống chính khóa/ngoài giờ" tại trường cho tới khi làm rõ ranh giới.
- 🔗 Tích hợp dữ liệu thị trường lao động quốc gia (Luật 74/2025) → thiết kế adapter, MVP dùng dataset tĩnh.

### §9.5. AI & nền tảng số (Luật AI 134/2025, Luật GDĐT 20/2023, VNeID) — NFR bắt buộc
- **Human-in-the-loop**: AI chỉ **gợi ý có lý do**, người dùng/giáo viên/giám hộ ra quyết định cuối — không tự động hóa quyết định phân luồng/chọn nghề (Luật 134/2025 Đ.4 + nguyên tắc "không ép buộc" TT 16/2026).
- **Explainability + AI-disclosure**: mỗi khuyến nghị hiển thị **lý do** và nhãn **"được hỗ trợ bởi AI"**; lưu **model card/hồ sơ kỹ thuật** (mục đích, dữ liệu, giới hạn, kiểm soát rủi ro).
- **Bias testing** bộ trắc nghiệm & thuật toán (giới/vùng miền/hoàn cảnh); kiểm thử công bằng định kỳ, tài liệu hóa.
- **Phân loại rủi ro AI + thông báo Bộ KH&CN** (Đ.9–10) đưa vào **checklist go-live**; nếu rủi ro cao → đánh giá sự phù hợp (Đ.13).
- **Gắn nhãn nội dung do AI tạo** (Đ.11) nếu sinh văn bản/hình ảnh tư vấn.
- **e-consent có giá trị pháp lý** (Luật GDĐT 20/2023); để ngỏ chữ ký điện tử giám hộ.
- **Quản trị & đánh giá rủi ro dữ liệu** (Luật Dữ liệu 60/2024 + **NĐ 165/2025**): phân loại dữ liệu nền tảng, đối chiếu tiêu chí **dữ liệu quan trọng/cốt lõi**, lập quy trình **đánh giá rủi ro dữ liệu định kỳ hằng năm** — gắn vào DPIA & vận hành.
- **Adapter định danh & CSDL ngành GD** (TT 42/2021, VNeID NĐ 69/2024, Luật 123/2025 Đ.19 k.4, **NĐ 88/2026** — mã số hồ sơ học tập suốt đời Đ.9, kết nối có kiểm soát Đ.17) — kiến trúc để ngỏ, không bắt buộc MVP. *Chuẩn kết nối/chia sẻ tham chiếu: **NĐ 194/2025** (CSDL dùng chung, dữ liệu mở) + **QĐ 2439/QĐ-TTg** (Khung kiến trúc dữ liệu QG, Từ điển dữ liệu dùng chung v1.0).*

---

## §10. Bản đồ "căn cứ pháp lý → tính năng"

| Tính năng WeUp Career | Căn cứ nhu cầu | Ràng buộc tuân thủ |
|---|---|---|
| Tài khoản đa người dùng | — | NĐ 147/2024 (giám hộ < 16t), Luật 91/2025 (consent) |
| Nền tảng số hướng nghiệp (toàn bộ) | **TT 16/2026 Đ.5đ** (CNTT/chuyển đổi số = nội dung bắt buộc), NQ 71, QĐ 1705 NV8 | Luật 91/2025 (BVDLCN) |
| Thông tin nghề nghiệp / ngành / trường | **TT 16/2026 Đ.5a**, TT 07/2022 | Minh bạch nguồn |
| Trắc nghiệm định hướng (RIASEC/MBTI) | **TT 16/2026 Đ.5b**, CT 29 (khuyến khích AI/dữ liệu) | Luật 91/2025 (kết quả = nhạy cảm tiềm năng) |
| Kỹ năng lựa chọn nghề & ra quyết định | **TT 16/2026 Đ.5c**, TT 07/2022 | — |
| Trải nghiệm nghề nghiệp | **TT 16/2026 Đ.5d** | — |
| Gợi ý phân luồng (học tiếp / nghề / lao động) | **Luật 123/2025** (phân luồng trên nền hướng nghiệp), QĐ 525 (100% HS đến 2030) | TT 16/2026 (không ép buộc) + minh bạch thuật toán + BVDLCN |
| Hồ sơ hướng nghiệp theo cấp học | TT 07/2022, TT 16/2026 (phù hợp từng cấp), Luật GD 2019 | Luật 91/2025 (dữ liệu cá nhân/nhạy cảm) |
| Lộ trình kỹ năng & nghề | **Luật GDNN 124/2025** (trường trung học nghề, liên thông), Bộ luật LĐ 2019 | — |
| Thông tin thị trường lao động | Luật Việc làm 74/2025 (Đ.19) | NĐ 352/2025 nếu thành trung gian việc làm |
| Kênh trường học / tư vấn học đường | **TT 18/2025** (tư vấn hướng nghiệp & việc làm trong trường), TT 20/2023, QĐ 525 | Phân quyền + BVDLCN dữ liệu HS + nguyên tắc bảo mật/tự nguyện (TT 18/2025) |
| **Lõi khuyến nghị bằng AI** (gợi ý ngành/nghề/lộ trình) | **Luật 123/2025 Đ.19** (AI có kiểm soát), NQ 71, QĐ 1705 NV8 | **★★ Luật AI 134/2025** (human-in-the-loop, minh bạch/giải trình, không thiên lệch, nhật ký, phân loại rủi ro + thông báo Bộ KH&CN) + BVDLCN |
| e-consent / chữ ký điện tử giám hộ | NĐ 147/2024, Luật 91/2025 | **Luật GDĐT 20/2023** (giá trị pháp lý thông điệp dữ liệu/chữ ký điện tử) |
| Xác thực giám hộ & độ tuổi | NĐ 147/2024 (trẻ <16t qua giám hộ) | **NĐ 69/2024 (VNeID)** — mức tài khoản theo tuổi; giá trị chứng minh như giấy tờ |
| Nội dung & đánh giá năng lực số cho HS | **TT 16/2026 Đ.5đ**, **TT 02/2025** (Khung năng lực số người học) | — |
| Hồ sơ kỹ năng/năng lực người dùng (số + ngoại ngữ) | **TT 02/2025** (năng lực số), **TT 33/2026** (khung năng lực ngoại ngữ 6 bậc — ⏳ hiệu lực 31/5/2026) | — |
| Cá nhân hóa gợi ý theo hồ sơ học tập | **TT 22/2021** (đánh giá HS THCS/THPT — nguồn học lực/năng lực/phẩm chất) | Luật 91/2025 (dữ liệu học tập = dữ liệu cá nhân) |
| Học liệu/nội dung hướng nghiệp trực tuyến (ĐH / người đi làm) | **TT 30/2023** (đào tạo trực tuyến GDĐH), TT 16/2026 | An toàn TT cá nhân + ANM + SHTT (TT 30/2023); BVDLCN |
| Công cụ/đào tạo cho giáo viên–tư vấn viên (B2B2C) | **TT 18/2026** (khung năng lực số giáo viên, Miền 6 = AI), TT 18/2025, TT 20/2023 | Luật AI 134/2025 (AI có đạo đức) + BVDLCN |
| Nội dung kỹ năng tổ chức trong trường (nếu có) | TT 16/2026 Đ.5c | **⚠ TT 04/2014** (cấp phép hoạt động GD kỹ năng sống) — xem §9.4 |
| Đồng bộ hồ sơ số / định danh người học | **QĐ 131/QĐ-TTg**, **TT 42/2021** (CSDL GD, mã định danh), Luật 123/2025 Đ.19 k.4, **★★ NĐ 88/2026** (mã số hồ sơ học tập suốt đời Đ.9, hồ sơ liên thông VNeID Đ.12) | **NĐ 88/2026 Đ.4** (tổ chức khác bảo vệ quyền chủ thể) + **Đ.17** (kết nối có kiểm soát) + Luật Dữ liệu 60/2024 + BVDLCN |
| Học liệu/nội dung hướng nghiệp trực tuyến (trong trường) | **TT 09/2021** (dạy học trực tuyến), TT 16/2026 | BVDLCN dữ liệu HS |

---

## §11. Nguồn tham khảo (Sources)

**Khối A — Giáo dục hướng nghiệp (theo tầng VBPL):**

*Tầng Đảng:*
- [Toàn văn NQ 71-NQ/TW (22/8/2025) — đột phá phát triển GD&ĐT](https://xaydungchinhsach.chinhphu.vn/toan-van-nghi-quyet-so-71-nq-tw-cua-bo-chinh-tri-ve-dot-pha-phat-trien-giao-duc-va-dao-tao-119250828110759964.htm) · [Hệ thống Văn kiện Đảng](https://tulieuvankien.dangcongsan.vn/he-thong-van-ban/van-ban-cua-dang/nghi-quyet-so-71-nqtw-ngay-2282025-cua-bo-chinh-tri-ve-dot-pha-phat-trien-giao-duc-va-dao-tao-11771)
- [Chỉ thị 29-CT/TW (05/01/2024)](https://xaydungchinhsach.chinhphu.vn/)

*Tầng Quốc hội:*
- [Luật Giáo dục 2019 (43/2019/QH14)](https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-giao-duc-2019-367665.aspx)
- ★ [Luật Giáo dục sửa đổi 2025 (123/2025/QH15) — LuatVietnam](https://luatvietnam.vn/giao-duc/luat-giao-duc-sua-doi-2025-so-123-2025-qh15-422918-d1.html) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=216504&classid=1&typegroupid=3) · [Toàn văn — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Luat-Giao-duc-sua-doi-2025-so-123-2025-QH15-656970.aspx) · [Phân tích Điều 19 (AI & chuyển đổi số)](https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/chinh-sach-moi/103519/nha-nuoc-khuyen-khich-giao-duc-bang-tri-tue-nhan-tao-theo-luat-giao-duc-sua-doi-2025) · *(Điều 19 = căn cứ tầng Luật cho lõi số/AI; Điều 12 = bằng trung học nghề)*
- [VBHN 72/VBHN-VPQH 2026 — hợp nhất Luật Giáo dục](https://luatvietnam.vn/giao-duc/van-ban-hop-nhat-72-vbhn-vpqh-2026-hop-nhat-luat-giao-duc-430278-d5.html)

*Tầng Chính phủ / Thủ tướng:*
- [QĐ 1705/QĐ-TTg (31/12/2024) — Chiến lược phát triển GD đến 2030, tầm nhìn 2045](https://xaydungchinhsach.chinhphu.vn/quyet-dinh-1705-qd-ttg-chien-luoc-phat-trien-giao-duc-den-nam-2030-tam-nhin-2045-119250102173414127.htm)
- ★ [QĐ 131/QĐ-TTg (25/01/2022) — Đề án tăng cường ứng dụng CNTT & chuyển đổi số trong GD&ĐT 2022–2025, định hướng 2030 — Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=205236&classid=0) · [LuatVietnam](https://luatvietnam.vn/khoa-hoc/quyet-dinh-131-qd-ttg-216285-d1.html) · *(người học/nhà giáo làm trung tâm; 2025 = 100% người học có hồ sơ số + mã định danh thống nhất; nêu "tự học với trợ lý ảo")*
- [QĐ 525/QĐ-TTg (06/3/2025) — Kế hoạch thực hiện CT 29 đến 2030](https://luatvietnam.vn/giao-duc/quyet-dinh-525-qd-ttg-2025-ke-hoach-thuc-hien-chi-thi-29-ct-tw-pho-cap-giao-duc-den-nam-2030-393107-d1.html)
- [Kế hoạch triển khai Luật 123/2025 (QĐ 108/QĐ-TTg, 16/01/2026)](https://baochinhphu.vn/ban-hanh-ke-hoach-trien-khai-thi-hanh-luat-sua-doi-bo-sung-mot-so-dieu-cua-luat-giao-duc-102260116181009678.htm)
- ★★ [NĐ 88/2026/NĐ-CP (ký 28/3/2026, hiệu lực 15/5/2026) — Quản lý dữ liệu giáo dục & đào tạo; vận hành CSDL quốc gia về GD&ĐT (5 chương 25 điều) — LuatVietnam](https://luatvietnam.vn/giao-duc/nghi-dinh-88-2026-nd-cp-quan-ly-du-lieu-giao-duc-va-dao-tao-430659-d1.html) · [HoaTieu](https://hoatieu.vn/van-ban-phap-luat/nghi-dinh-88-2026-nd-cp-quan-ly-du-lieu-giao-duc-dao-tao) · *(căn cứ đồng thời Luật Dữ liệu 60/2024 + GDĐT 20/2023 + BVDLCN 91/2025 + GD 43/2019 & 123/2025; Đ.9 mã số hồ sơ học tập suốt đời theo số định danh cá nhân; Đ.12 liên thông VNeID; Đ.4 tổ chức khác bảo vệ quyền chủ thể; Đ.8 lưu trữ vĩnh viễn — của Nhà nước; Đ.17 kết nối CSDL dân cư/DN/BHXH/y tế; lộ trình mã số trước 01/01/2027)*
- ⛔ [QĐ 522/QĐ-TTg — Đề án hướng nghiệp & phân luồng 2018–2025 (đã kết thúc chu kỳ)](https://vanban.chinhphu.vn/?pageid=27160&docid=193706)

*Tầng Bộ:*
- ★ [Toàn văn TT 16/2026/TT-BGDĐT (24/3/2026) — Cổng Chính phủ](https://xaydungchinhsach.chinhphu.vn/toan-van-thong-tu-16-2026-tt-bgddt-quy-dinh-ve-huong-nghiep-va-phan-luong-trong-giao-duc-119260326152952197.htm) · [LuatVietnam](https://luatvietnam.vn/giao-duc/thong-tu-16-2026-tt-bgddt-quy-dinh-huong-nghiep-va-phan-luong-giao-duc-429865-d1.html) · [Báo Chính phủ](https://baochinhphu.vn/quy-dinh-moi-ve-huong-nghiep-phan-luong-trong-giao-duc-102260326163022159.htm)
- [Thông tư 07/2022/TT-BGDĐT — tư vấn nghề nghiệp, việc làm, khởi nghiệp](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-07-2022-TT-BGDDT-cong-tac-tu-van-nghe-nghiep-viec-lam-ho-tro-khoi-nghiep-512260.aspx)
- [Thông tư 32/2018/TT-BGDĐT — Chương trình GDPT 2018 (HĐTN-HN bắt buộc 105 tiết/năm)](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-32-2018-TT-BGDDT-Chuong-trinh-giao-duc-pho-thong-403454.aspx)
- ★ [Thông tư 18/2025/TT-BGDĐT (15/9/2025, hiệu lực 31/10/2025) — tư vấn học đường & công tác xã hội trong trường học, thay thế TT 31/2017 + TT 33/2018](https://vanban.chinhphu.vn/?pageid=27160&docid=215348) · [Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-18-2025-TT-BGDDT-huong-dan-cong-tac-xa-hoi-trong-truong-hoc-672882.aspx)
- ⛔ [Thông tư 31/2017/TT-BGDĐT — tư vấn tâm lý cho học sinh (đã bị TT 18/2025 thay thế — tham chiếu lịch sử)](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-31-2017-TT-BGDDT-huong-dan-cong-tac-tu-van-tam-ly-cho-hoc-sinh-truong-pho-thong-374431.aspx)

*Tầng Bộ — chuyển đổi số trong giáo dục (nền cho hình thái sản phẩm):*
- ★ [TT 02/2025/TT-BGDĐT (ký 24/01/2025, hiệu lực 11/3/2025) — Khung năng lực số cho người học (6 miền / 24 năng lực thành phần / 4 trình độ / 8 bậc) — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-02-2025-TT-BGDDT-quy-dinh-Khung-nang-luc-so-cho-nguoi-hoc-625668.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=212648)
- [TT 42/2021/TT-BGDĐT (ký 30/12/2021, hiệu lực 14/2/2022) — CSDL giáo dục & đào tạo; mã định danh duy nhất, bất biến, thống nhất xuyên suốt cấp học (Điều 10); thay thế TT 26/2019 — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Thong-tu-42-2021-TT-BGDDT-co-so-du-lieu-giao-duc-va-dao-tao-493270.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=205058&classid=1&typegroupid=6)
- [TT 09/2021/TT-BGDĐT (ký 30/3/2021, hiệu lực 16/5/2021) — quản lý & tổ chức dạy học trực tuyến (GDPT & GDTX cấp THCS/THPT) — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-09-2021-TT-BGDDT-quan-ly-va-to-chuc-day-hoc-truc-tuyen-trong-co-so-giao-duc-pho-thong-449937.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/default.aspx?pageid=27160&docid=203106)
- [TT 30/2023/TT-BGDĐT (ký 29/12/2023, hiệu lực 13/2/2024) — ứng dụng CNTT trong đào tạo trực tuyến đối với giáo dục đại học; thay thế TT 12/2016 — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-30-2023-TT-BGDDT-ung-dung-cong-nghe-thong-tin-trong-dao-tao-truc-tuyen-giao-duc-dai-hoc-595956.aspx) · *(phần mềm dạy học đồng bộ/không đồng bộ, LMS/LCMS, MOOC; học liệu thẩm định; an toàn TT cá nhân + ANM + SHTT — đồng hành TT 09/2021 cho phân khúc ĐH/người đi làm)*
- ★ [TT 33/2026/TT-BGDĐT (ký 15/4/2026, hiệu lực 31/5/2026) — Khung năng lực ngoại ngữ dùng cho Việt Nam; thay thế Khung 01/2014; tham chiếu CEFR 2020–2021, 3 cấp/6 bậc + Pre-A1, khung cũ dùng tới 31/12/2027 — LuatVietnam](https://luatvietnam.vn/giao-duc/thong-tu-33-2026-tt-bgddt-khung-nang-luc-ngoai-ngu-dung-cho-viet-nam-430000-d1.html) · [Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-33-2026-TT-BGDDT-Khung-nang-luc-ngoai-ngu-dung-cho-Viet-Nam.aspx) · *(⏳ chưa có hiệu lực đến 31/5/2026 — xem §8.1; chuẩn năng lực ngoại ngữ đi kèm TT 02/2025 Khung năng lực số)*
- [TT 22/2021/TT-BGDĐT (20/7/2021, hiệu lực 05/9/2021) — đánh giá học sinh THCS & THPT; thay thế TT 58/2011 + 26/2020 — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-22-2021-TT-BGDDT-danh-gia-hoc-sinh-trung-hoc-co-so-va-trung-hoc-pho-thong-207846.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=203926) · *(nguồn dữ liệu hồ sơ học tập để cá nhân hóa gợi ý hướng nghiệp — dữ liệu cá nhân, áp Khối C)*
- ⚠ [TT 04/2014/TT-BGDĐT (28/2/2014, hiệu lực 15/4/2014, còn hiệu lực) — quản lý hoạt động giáo dục kỹ năng sống & hoạt động giáo dục ngoài giờ chính khóa — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Giao-duc/Thong-tu-04-2014-TT-BGDDT-quan-ly-hoat-dong-giao-duc-ky-nang-song-hoat-dong-giao-duc-ngoai-gio-chinh-khoa-223200.aspx) · *(yêu cầu cấp phép Sở GD&ĐT/hiệu trưởng để tổ chức hoạt động GD kỹ năng sống trong trường — ràng buộc B2B2C tiềm năng, xem §9.4)*
- [TT 18/2026/TT-BGDĐT (ký 27/3/2026, hiệu lực 12/5/2026) — Khung năng lực số đối với giáo viên & cán bộ quản lý cơ sở GD mầm non/phổ thông/GDTX (6 miền/20 năng lực/3 mức; Miền 6 = AI) — Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=217451) · [LuatVietnam](https://luatvietnam.vn/giao-duc/thong-tu-18-2026-tt-bgddt-khung-nang-luc-so-cho-giao-vien-va-can-bo-quan-ly-430564-d1.html) · *(bản song hành phía nhà giáo của TT 02/2025 — kênh B2B2C giáo viên)*

**Khối B — Việc làm & nghề nghiệp:**
- [Luật Việc làm 2025 (74/2025/QH15) — toàn văn](https://thuvienphapluat.vn/van-ban/Lao-dong-Tien-luong/Luat-Viec-lam-2025-so-74-2025-QH15-530912.aspx)
- [Toàn văn Luật Việc làm — Cổng Chính phủ](https://xaydungchinhsach.chinhphu.vn/toan-van-luat-viec-lam-119250711173403835.htm)
- [Nghị định 318/2025/NĐ-CP — đăng ký lao động & HTTT TTLĐ](https://luatvietnam.vn/lao-dong/nghi-dinh-318-2025-nd-cp-quy-dinh-chi-tiet-luat-viec-lam-ve-dang-ky-lao-dong-va-thong-tin-thi-truong-421247-d1.html)
- [Các thông tin trên HTTT thị trường lao động từ 01/01/2026](https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/chinh-sach-moi/100593/cac-thong-tin-co-tren-he-thong-thong-tin-thi-truong-lao-dong-tu-01-01-2026)
- ★ [Luật Giáo dục nghề nghiệp 2025 (124/2025/QH15, hiệu lực 01/01/2026, thay thế 74/2014) — LuatVietnam](https://luatvietnam.vn/giao-duc/luat-giao-duc-nghe-nghiep-2025-so-124-2025-qh15-422919-d1.html) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=216505&classid=1&orggroupid=1) · [Công báo](https://congbao.chinhphu.vn/van-ban/luat-so-124-2025-qh15-468685.htm)
- ⛔ [Luật Giáo dục nghề nghiệp 2014 (74/2014/QH13) — đã bị 124/2025 thay thế, tham chiếu lịch sử](https://thuvienphapluat.vn/van-ban/Lao-dong-Tien-luong/Luat-Giao-duc-nghe-nghiep-2014-259733.aspx)

**Khối C — Dữ liệu cá nhân & trẻ em:**
- [Luật Bảo vệ dữ liệu cá nhân 2025 (91/2025/QH15)](https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-Bao-ve-du-lieu-ca-nhan-2025-so-91-2025-QH15-625628.aspx)
- [Luật BVDLCN — Cổng Chính phủ](https://chinhphu.vn/?pageid=27160&docid=214590)
- [Nghị định 13/2023/NĐ-CP (đã hết hiệu lực — tham chiếu lịch sử)](https://vanban.chinhphu.vn/?pageid=27160&docid=207759)
- [Nghị định 147/2024/NĐ-CP — quản lý Internet & mạng xã hội](https://lsvn.vn/nghi-dinh-147-2024-nd-cp-cu-hich-quan-ly-internet-va-mang-xa-hoi-tai-viet-nam-a150984.html)
- [NĐ 147 — trẻ < 16 tuổi đăng ký qua cha mẹ](https://lsvn.vn/tu-15-12-2024-tre-duoi-16-tuoi-dang-ky-tai-khoan-mang-xa-hoi-bang-thong-tin-cua-cha-me-a149746.html)
- [Bảo vệ trẻ em trên môi trường mạng (Luật Trẻ em 2016 Đ.54, Luật ANM 2018 Đ.29)](https://vtv.vn/xa-hoi/nhieu-quy-dinh-moi-nham-bao-ve-tre-em-tren-moi-truong-mang-20241128121446559.htm)

**Khối D — Nền tảng số, Dữ liệu, Công nghệ số & AI:**
- ★★ [Luật Trí tuệ nhân tạo 2025 (134/2025/QH15, thông qua 10/12/2025, hiệu lực 01/3/2026) — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Luat-Tri-tue-nhan-tao-2025-so-134-2025-QH15-679013.aspx) · [LuatVietnam (toàn văn)](https://luatvietnam.vn/tin-van-ban-moi/da-co-toan-van-luat-tri-tue-nhan-tao-2025-so-134-2025-qh15-186-106127-article.html) · [Tóm lược chính sách](https://thuvienphapluat.vn/chinh-sach-phap-luat-moi/vn/ho-tro-phap-luat/chinh-sach-moi/101526/da-co-luat-tri-tue-nhan-tao-2025-luat-so-134-2025-qh15) · *(8 chương 35 điều; Đ4 nguyên tắc con-người-làm-trung-tâm; Đ9 phân loại rủi ro; Đ33 bãi bỏ Chương IV của Luật CNCNS 71/2025; cơ quan: Bộ KH&CN)*
- [Luật Dữ liệu 2024 (60/2024/QH15, thông qua 30/11/2024, hiệu lực 01/7/2025) — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-Du-lieu-2024-so-60-2024-QH15-621343.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=212488&classid=1&orggroupid=1) · [Toàn văn (xaydungchinhsach)](https://xaydungchinhsach.chinhphu.vn/toan-van-luat-du-lieu-119250226145839949.htm) · *(Trung tâm dữ liệu quốc gia, CSDL tổng hợp quốc gia, dữ liệu xuyên biên giới — phân biệt với Luật BVDLCN 91/2025)*
- [Luật Giao dịch điện tử 2023 (20/2023/QH15, thông qua 22/6/2023, hiệu lực 01/7/2024) — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Luat-Giao-dich-dien-tu-2023-20-2023-QH15-513347.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=208421) · *(giá trị pháp lý của thông điệp dữ liệu, chữ ký điện tử/số, hợp đồng điện tử — nền cho e-consent & chữ ký điện tử giám hộ; thay thế Luật GDĐT 2005)*
- [Luật Công nghiệp công nghệ số 2025 (71/2025/QH15, thông qua 14/6/2025, hiệu lực 01/01/2026) — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Luat-Cong-nghiep-cong-nghe-so-2025-so-71-2025-QH15-621341.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=214609&classid=1&typegroupid=3) · ⚠ *(6 chương 51 điều; Chương IV về AI **đã bị Luật AI 134/2025 Đ.33 bãi bỏ** — không viện dẫn Ch IV làm căn cứ AI; phần tài sản số / bán dẫn / cơ chế thử nghiệm có kiểm soát vẫn hiệu lực — xem §8.4)*
- [NĐ 69/2024/NĐ-CP (ký 25/6/2024, hiệu lực 01/7/2024) — định danh & xác thực điện tử (VNeID); thay thế NĐ 59/2022; Cục C06 Bộ Công an](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Nghi-dinh-69-2024-ND-CP-quy-dinh-dinh-danh-xac-thuc-dien-tu-597437.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=210491) · *(trẻ em được cấp tài khoản RIÊNG; mốc tuổi VNeID 6/14 khác mốc <16 của NĐ 147/2024)*
- ★ [NĐ 165/2025/NĐ-CP (30/6/2025, hiệu lực 01/7/2025) — quy định chi tiết một số điều của Luật Dữ liệu 60/2024 — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Nghi-dinh-165-2025-ND-CP-huong-dan-Luat-Du-lieu-664344.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=214321) · *(áp dụng rộng cả tổ chức trong & ngoài nước; quản lý rủi ro dữ liệu, dữ liệu quan trọng/cốt lõi, đánh giá rủi ro hằng năm, lưu trữ — có thể áp cho WeUp Career; phân biệt với NĐ 356/2025 thi hành Luật BVDLCN)*
- [NĐ 194/2025/NĐ-CP (03/7/2025, hiệu lực 19/8/2025) — quy định chi tiết Luật Giao dịch điện tử về CSDL dùng chung, kết nối/chia sẻ dữ liệu, dữ liệu mở, Khung kiến trúc tổng thể quốc gia số — Thư viện Pháp luật](https://thuvienphapluat.vn/van-ban/Cong-nghe-thong-tin/Nghi-dinh-194-2025-ND-CP-huong-dan-Luat-Giao-dich-dien-tu-664628.aspx) · [Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=214470) · *(chủ yếu điều chỉnh cơ quan nhà nước — tham chiếu kỹ thuật cho adapter kết nối hệ thống nhà nước)*
- [QĐ 2439/QĐ-TTg (04/11/2025) — Khung kiến trúc dữ liệu quốc gia + Khung quản trị/quản lý dữ liệu quốc gia + Từ điển dữ liệu dùng chung v1.0 — Cổng Chính phủ](https://vanban.chinhphu.vn/?pageid=27160&docid=215780) · *(áp cho hệ thống chính trị/cơ quan nhà nước; nguyên tắc "lưu trữ tối thiểu / thu thập một lần / chia sẻ minh bạch" — tham chiếu chuẩn dữ liệu cho adapter CSDLQG, không ràng buộc trực tiếp)*

---

## §12. Việc cần làm tiếp (Open items)

**Đã hoàn thành (tham chiếu lịch sử rà soát):**

- [x] ~~Xác minh số hiệu & ngày của QĐ 525 & CT 29~~ → **QĐ 525/QĐ-TTg = 06/3/2025**; **CT 29-CT/TW = 05/01/2024** (đã xác minh qua nguồn chính thống 2026-05-28).
- [x] ~~Bổ sung 7 VBPL mới (2024–2026)~~ → đã tích hợp TT 16/2026, Luật 123/2025, NQ 71, QĐ 1705, QĐ 108, NĐ 37/2025, TT 31/2017 vào Khối A (2026-05-28).
- [x] ~~Tích hợp TT 18/2025/TT-BGDĐT~~ → **TT 18/2025 thay thế TT 31/2017 + TT 33/2018** (hiệu lực 31/10/2025); đã cập nhật §4.4, §9, §10 (2026-05-28). TT 31/2017 chuyển thành tham chiếu lịch sử.
- [x] ~~Tổ chức thư viện nguồn tham khảo chính thống~~ → đã lập **`docs/research/sources.md`** (~70 nguồn VN + quốc tế) (2026-05-28).
- [x] ~~Tích hợp `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md`~~ → phát hiện & xác minh **Luật GDNN 124/2025/QH15** (hiệu lực 01/01/2026) **thay thế Luật GDNN 74/2014**, đưa **"trường trung học nghề"** vào hệ thống GD quốc dân; bổ sung **TT 32/2018** (CT GDPT 2018, HĐTN-HN 105 tiết/năm). Đã cập nhật §4.4, §5, §9, §10 (2026-05-28).
- [x] ~~Kiểm tra & phân tích sâu Luật 123/2025/QH15~~ → **Điều 19** = căn cứ **tầng Luật (Quốc hội)** cho lõi số/AI (k.3 AI có kiểm soát, k.4 chuyển đổi số toàn diện + CSDLQG về GD&ĐT, k.5 ưu tiên phát triển AI); **Điều 12** bổ sung **"bằng trung học nghề"**. Đã cập nhật §4.2, §4.5, §10 (2026-05-28). *Lưu ý mở:* điều khoản chuyển tiếp Điều 34 (bằng THCS cấp trước 01/01/2026 vẫn có giá trị) — kiểm tra khi mô hình hóa văn bằng THCS (xem §8.2).
- [x] ~~Nghiên cứu lớp pháp lý nền tảng số / dữ liệu / công nghệ số & AI~~ → đã lập **Khối D** (§7): **★★ Luật AI 134/2025**, **Luật Dữ liệu 60/2024**, **Luật GDĐT 20/2023**, **Luật CNCNS 71/2025**, **NĐ 69/2024 (VNeID)**; + 3 thông tư chuyển đổi số GD vào Khối A tầng Bộ + **QĐ 131/QĐ-TTg**. Đã cập nhật §1, §4.3, §4.4, §7, §9, §10, §11 (2026-05-28). *Đính chính:* TT 09/2021 hiệu lực **16/5/2021**; NĐ 69/2024 — trẻ được cấp **tài khoản RIÊNG**, mốc tuổi VNeID 6/14 ≠ mốc <16 NĐ 147/2024.
- [x] ~~Cập nhật **NĐ 88/2026/NĐ-CP**~~ → đã xác minh (3 vòng): **ký 28/3/2026, hiệu lực 15/5/2026, 5 chương 25 điều**; văn bản **vận hành CSDLQG về GD&ĐT**. Đặt ở **§4.3 Khối A Tầng Chính phủ** (quy ước: VBPL ngành GD xếp theo tầng trong Khối A). Đã cập nhật §1, §4.3, §9.1, §9.3, §9.5, §10, §11. **Luật Tổ chức Chính phủ 63/2025/QH15** — độ liên quan thấp, **không bổ sung**.
- [x] ~~Kiểm tra 6 VBPL bổ sung (2439/QĐ-TTg, 22/2025/TT-BKHCN, 194/2025/NĐ-CP, 165/2025/NĐ-CP, 738/QĐ-BGDĐT, 60/2024/QH15)~~ → phán quyết (2026-05-28): **(1) 60/2024** Luật Dữ liệu — đã có. **(2) ★ NĐ 165/2025** — CÓ LIÊN QUAN, đã thêm §7+§11 (đánh giá rủi ro dữ liệu hằng năm). **(3) NĐ 194/2025** — liên quan gián tiếp, đã thêm (tham chiếu kỹ thuật adapter). **(4) QĐ 2439/QĐ-TTg** — đã thêm (tham chiếu chuẩn dữ liệu). **(5) 22/2025/TT-BKHCN** — KHÔNG thêm (lĩnh vực KHCN). **(6) 738/QĐ-BGDĐT** — KHÔNG thêm (hành chính nội bộ).
- [x] ~~Rà soát **toàn bộ** kho VBPL Bộ GD&ĐT trên moet.gov.vn (31 trang)~~ → thu thập & phân loại **684 văn bản** (2026-05-28). **Bổ sung 5 thông tư** (§4.4/§9/§10/§11): **★ TT 33/2026** (khung ngoại ngữ); **⚠ TT 04/2014** (cấp phép GD kỹ năng sống); **TT 30/2023** (đào tạo trực tuyến GDĐH); **TT 22/2021** (đánh giá HS THCS/THPT); **TT 18/2026** (khung năng lực số giáo viên). **Loại trừ:** chuẩn nghề nghiệp/xếp lương; chọn SGK; quy chế thi/tuyển sinh; tiếng dân tộc; GDQP-AN; mầm non; mua sắm CNTT; tư vấn du học; TT 26/2019 (đã bị 42/2021 thay); TT 13/2022, 17/2025, 20/2021 (sửa CT GDPT — housekeeping).
- [x] ~~Rà soát lại toàn bộ nội dung & **tính hiệu lực** của mọi văn bản + tổ chức lại theo chuẩn học thuật~~ → đã hoàn thành (2026-05-28): thang 6 trạng thái hiệu lực (§0.4), bảng tổng hợp toàn bộ văn bản kèm cột tình trạng (§3), **phân tích quan hệ hiệu lực & chuỗi thay thế (§8)**. **Phát hiện chốt: TT 33/2026 ⏳ chưa có hiệu lực đến 31/5/2026.** Tái cấu trúc §0–§12; cập nhật mọi tham chiếu chéo.

**Còn lại (theo thứ tự ưu tiên cho redesign `docs/spec.md`):**

- [ ] Làm rõ **điều kiện kết nối CSDLQG về GD&ĐT** (NĐ 88/2026 Đ.17) cho tổ chức ngoài Nhà nước: thủ tục, cấp phép, mức độ chia sẻ — và chốt **ranh giới lưu trữ vĩnh viễn (Đ.8) vs quyền xóa/tối thiểu hóa BVDLCN** trong DPIA trước khi thiết kế adapter định danh.
- [ ] Đối chiếu **NĐ 165/2025** (quản lý rủi ro dữ liệu, đánh giá rủi ro hằng năm, dữ liệu quan trọng/cốt lõi) với phạm vi WeUp Career: xác định dữ liệu nền tảng có thuộc "dữ liệu quan trọng" không, lập **quy trình đánh giá rủi ro dữ liệu định kỳ** — đầu vào cho NFR §9.5 + DPIA.
- [ ] Đọc **toàn văn Luật AI 134/2025 Chương II (Đ9–15)** để **tự phân loại mức rủi ro AI** của lõi khuyến nghị (cao/trung bình/thấp) + xác định nghĩa vụ thông báo Bộ KH&CN + hồ sơ kỹ thuật — đầu vào trực tiếp cho NFR §9.5.
- [ ] Lập **checklist tuân thủ AI khi go-live** (human-in-the-loop, AI-disclosure, gắn nhãn nội dung AI, nhật ký khuyến nghị, kiểm thử thiên lệch) từ Luật AI 134/2025 Đ4/Đ9/Đ26–27 — gắn vào quy trình phát hành.
- [ ] Đánh giá **khả thi tích hợp VNeID** (NĐ 69/2024) cho xác thực giám hộ & độ tuổi: điều kiện kết nối, mức tài khoản cần thiết, ràng buộc — quyết định đưa vào MVP hay giai đoạn sau.
- [ ] Đọc **toàn văn TT 16/2026/TT-BGDĐT** (6 chương 21 điều) để rút chi tiết Điều 8 (trách nhiệm cơ sở GD), điều kiện bảo đảm, biện pháp phân luồng — phục vụ thiết kế module phân luồng.
- [ ] Đọc **toàn văn Điều 20 Luật 91/2025 + NĐ 356/2025** để chốt chi tiết cơ chế đồng ý của trẻ em (đối chiếu mốc 7 tuổi / 16 tuổi).
- [ ] Rà soát **NĐ 352/2025** để xác định ranh giới "dịch vụ việc làm" cần cấp phép vs "thông tin định hướng" không cần.
- [ ] Đọc **toàn văn TT 18/2025** (Mục 1 Chương II) để thiết kế module B2B2C kênh trường học (vai trò `counselor`/`school_admin`) và quy trình tư vấn hướng nghiệp trong trường.
- [ ] Theo dõi mốc **TT 33/2026 hiệu lực 31/5/2026** (§8.1) — cập nhật trạng thái ⏳→✅ trong §3/§4.4 và changelog §0.5 sau ngày đó.
- [ ] Khi redesign `docs/spec.md`: nhúng (a) 5 nội dung Điều 5 TT 16/2026 làm khung module, (b) ràng buộc Khối C vào NFR quyền riêng tư & đồng ý, (c) **NFR Khối D §9.5** (human-in-the-loop, giải thích được + AI-disclosure, kiểm thử thiên lệch, phân loại rủi ro + thông báo Bộ KH&CN, gắn nhãn nội dung AI, e-consent/chữ ký điện tử, adapter định danh CSDL GD).
- [ ] Lập **DPIA template** trong `docs/legal/` trước khi viết code xử lý dữ liệu người dùng.
- [ ] Lưu trữ tài liệu nguồn `docs/temp/Cap_Nhat_Van_Ban_Phap_Quy.md` (đã rút trích xong) — cân nhắc chuyển vào `docs/legal/sources/`.
