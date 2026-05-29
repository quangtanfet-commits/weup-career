# Thư viện nguồn tham khảo — WeUp Career

> Thư mục nghiên cứu **có chú giải** phục vụ xây dựng nền tảng **Hướng nghiệp Quốc gia WeUp Career** (học sinh, sinh viên & người đi làm tại Việt Nam).
>
> **Ngày lập:** 2026-05-28 · **Cập nhật:** 2026-05-28 (tích hợp `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md` ⇒ bổ sung §14 số liệu thực chứng, §15 mô hình Singapore, §16 nút thắt & 6 đề xuất). · **Nguồn gốc:** chắt lọc & tổ chức lại từ `docs/temp/Tong_hop_nguon_tai_lieu.md` (bản tra cứu 12/05/2026) + `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md`.
> **Quan hệ tài liệu:** Phần **căn cứ pháp lý ràng buộc** (VBPL còn/​hết hiệu lực, ràng buộc thiết kế) nằm ở [`docs/legal/legal-basis.md`](../legal/legal-basis.md). Tài liệu này là **thư viện tri thức nền** (lý luận, mô hình, chuẩn năng lực, dữ liệu quốc tế, công cụ triển khai) để thiết kế **nội dung & sản phẩm** — bổ trợ chứ không thay thế legal-basis.

---

## 0. Cách dùng thư viện này

Phân tầng ưu tiên (theo bản đồ nguồn gốc):

1. **Ưu tiên 1 — Căn cứ chính thống:** VBPL, Chương trình GDPT, tài liệu do Bộ GD&ĐT / Chính phủ / ILO / OECD / UNESCO / Cedefop phát hành. Dùng làm căn cứ chính sách & nội dung.
2. **Ưu tiên 2 — Triển khai trong trường:** tài liệu tập huấn, cẩm nang, bộ công cụ dùng trực tiếp được.
3. **Ưu tiên 3 — Cơ sở lý luận:** bài báo khoa học, giáo trình, chuyên khảo để xây khung lý thuyết, mô hình & thang đo.

⚠️ **Lưu ý hiệu lực:** một số nguồn trong bản gốc đã **hết hiệu lực/​kết thúc chu kỳ** — QĐ 522/QĐ-TTg (Đề án 2018–2025) và TT 31/2017 (bị TT 18/2025 thay thế). Chúng vẫn có **giá trị tham chiếu lịch sử/​mô hình** (cơ sở dữ liệu nghề, ngày hội hướng nghiệp, thí điểm mô hình) nhưng **không dùng làm căn cứ pháp lý sống** — xem [`legal-basis.md`](../legal/legal-basis.md).

---

## 1. Nguồn Việt Nam — Pháp lý, chính sách & chương trình giáo dục

> VBPL trụ cột đã phân tích trong [`legal-basis.md`](../legal/legal-basis.md). Bảng dưới bổ sung **chương trình giáo dục** (chưa nằm trong legal-basis) làm nguồn lõi thiết kế nội dung.
>
> **★ Lớp pháp lý nền tảng số / dữ liệu / AI** (mới, 2026-05-28) — xem **Khối D** trong [`legal-basis.md` §7](../legal/legal-basis.md): **Luật AI 134/2025** (hiệu lực 01/3/2026), **Luật Dữ liệu 60/2024**, **Luật GDĐT 20/2023** (e-consent/chữ ký điện tử), **NĐ 69/2024 (VNeID)**, cùng 3 thông tư chuyển đổi số GD (**TT 02/2025** Khung năng lực số, **TT 42/2021** CSDL GD/mã định danh, **TT 09/2021** dạy học trực tuyến), **QĐ 131/QĐ-TTg** và **★★ NĐ 88/2026/NĐ-CP** (hiệu lực 15/5/2026 — vận hành CSDL quốc gia về GD&ĐT: mã số hồ sơ học tập suốt đời Đ.9, hồ sơ liên thông VNeID Đ.12, tổ chức khác bảo vệ quyền chủ thể Đ.4, kết nối có kiểm soát Đ.17). Bổ sung nghị định/quyết định hạ tầng dữ liệu (kiểm tra 2026-05-28): **★ NĐ 165/2025/NĐ-CP** (thi hành Luật Dữ liệu 60/2024 — áp rộng cả tư nhân, đánh giá rủi ro dữ liệu hằng năm, dữ liệu quan trọng), **NĐ 194/2025/NĐ-CP** (thi hành Luật GDĐT 20/2023 — CSDL dùng chung, dữ liệu mở; tham chiếu kỹ thuật), **QĐ 2439/QĐ-TTg** (Khung kiến trúc dữ liệu QG + Từ điển dữ liệu dùng chung v1.0). *(Đã kiểm tra nhưng KHÔNG đưa vào: 22/2025/TT-BKHCN — dữ liệu KHCN/ĐMST; 738/QĐ-BGDĐT — hành chính nội bộ Bộ.)* Trong đó **TT 02/2025 (Khung năng lực số: 6 miền / 24 năng lực)** còn là **chuẩn nội dung** để WeUp Career thiết kế & đánh giá năng lực số cho người học (gắn TT 16/2026 Đ.5đ) — dùng kèm bảng §9 khi soạn nội dung.
>
> **★ Rà soát toàn bộ kho VBPL Bộ GD&ĐT (2026-05-28):** đã quét toàn bộ trang `moet.gov.vn/van-ban/van-ban-quy-pham-phap-luat` (31 trang, 684 văn bản đơn nhất) để lọc văn bản liên quan. **5 thông tư mới được thêm vào [`legal-basis.md`](../legal/legal-basis.md)** (§4.4 Tầng Bộ, §9.4, §10, §11): **TT 33/2026** (Khung năng lực ngoại ngữ 6 bậc, hiệu lực 31/5/2026, thay Khung 01/2014, ánh xạ CEFR), **TT 04/2014** (⚠ cấp phép **giáo dục kỹ năng sống** trong nhà trường — ràng buộc B2B2C, còn hiệu lực), **TT 30/2023** (đào tạo trực tuyến GDĐH), **TT 22/2021** (đánh giá HS THCS/THPT — nguồn dữ liệu hồ sơ học tập), **TT 18/2026** (Khung năng lực số giáo viên: 6 miền/20 năng lực, Miền 6 = AI). Trong đó **TT 33/2026 (ngoại ngữ)** và **TT 18/2026 (năng lực số GV)** là **chuẩn nội dung dùng được** cùng TT 02/2025 khi thiết kế thư viện kỹ năng & module giáo viên. *(Đã loại các nhóm hành chính/không liên quan: chuẩn nghề nghiệp & mã số–xếp lương–chức danh nhà giáo, chọn SGK, quy chế thi/tuyển sinh, tiếng dân tộc, GDQP-AN, mầm non, mua sắm CNTT, du học, và các thông tư sửa đổi CT GDPT 32/2018 — xem `legal-basis.md` §12.)*

| # | Nguồn | Cơ quan | Năm | Giá trị cho WeUp Career | Link |
|---|---|---|---|---|---|
| 1 | **TT 16/2026/TT-BGDĐT** — hướng nghiệp & phân luồng | Bộ GD&ĐT | 2026 | ★ Văn bản pháp lý trung tâm. Điều 5 = 5 nội dung cốt lõi (khung module MVP). Xem legal-basis §4.4–4.5. | [CSDL Chính phủ](https://vanban.chinhphu.vn/?docid=217321&pageid=27160) · [Toàn văn](https://xaydungchinhsach.chinhphu.vn/toan-van-thong-tu-16-2026-tt-bgddt-quy-dinh-ve-huong-nghiep-va-phan-luong-trong-giao-duc-119260326152952197.htm) |
| 2 | **TT 18/2025/TT-BGDĐT** — tư vấn học đường & công tác xã hội | Bộ GD&ĐT | 2025 | ★ Nền tổ chức **dịch vụ tư vấn hướng nghiệp trong trường** (tổ/phòng tư vấn, nhân sự, phối hợp liên ngành). Thay thế TT 31/2017. Căn cứ vai trò `counselor`/`school_admin`. | [CSDL Chính phủ](https://vanban.chinhphu.vn/?docid=215348&pageid=27160) |
| 3 | **Chương trình GDPT tổng thể 2018** | Bộ GD&ĐT | 2018 | Xác định giai đoạn GD cơ bản ↔ GD định hướng nghề nghiệp; năng lực tự chủ, tự học, giải quyết vấn đề. Khung phân tầng cấp học cho nội dung. | [moet.gov.vn (PDF)](https://moet.gov.vn/content/vanban/Lists/VBPQ/Attachments/1483/vbhn-chuong-trinh-tong-the.pdf) |
| 4 | **CT GDPT — Hoạt động trải nghiệm, hướng nghiệp (HĐTN-HN)** | Bộ GD&ĐT | 2018 | **Nguồn lõi** thiết kế hoạt động hướng nghiệp trong trường: mạch nội dung, yêu cầu cần đạt, đánh giá năng lực định hướng nghề nghiệp. | [PDF](https://dienbien.edu.vn/uploads/doi-moi-chuong-trinh-gdpt/20ct_hoat-dong-trai-nghiem.pdf) |
| 5 | Luật Giáo dục 2019 (43/2019/QH14) | Quốc hội | 2019 | Căn cứ pháp lý chung. Xem legal-basis §4.2 (đã được sửa bởi Luật 123/2025). | [CSDL Chính phủ](https://vanban.chinhphu.vn/default.aspx?pageid=27160&docid=197310) |
| 6 | Thông cáo về Nghị định hướng nghiệp & phân luồng (đang phát triển) | Bộ GD&ĐT | 2025 | Theo dõi định hướng quản lý mới (nguyên tắc, biện pháp, học liệu địa phương). | [moet.gov.vn](https://moet.gov.vn/tintuc/Pages/thong-cao-bao-chi.aspx?ItemID=10831) |
| 7 | ⛔ QĐ 522/QĐ-TTg (Đề án 2018–2025) | Thủ tướng | 2018 | Đã hết chu kỳ. Tham chiếu **mô hình**: CSDL nghề, kết nối DN, ngày hội hướng nghiệp, thí điểm. | [CSDL Chính phủ](https://vanban.chinhphu.vn/default.aspx?docid=193710&pageid=27160) |

---

## 2. Nguồn Việt Nam — Tài liệu tập huấn, cẩm nang, bộ công cụ ứng dụng

> Nhóm **triển khai trực tiếp**. Bộ tài liệu **ILO Việt Nam** đặc biệt giá trị: là chuẩn nội dung/​công cụ hướng nghiệp đã được Bộ GD&ĐT đồng hành — dùng được làm nguồn nội dung cho thư viện nghề & bài tập trắc nghiệm.

| # | Nguồn | Cơ quan | Năm | Giá trị cho WeUp Career | Link |
|---|---|---|---|---|---|
| 1 | Tài liệu tập huấn HĐTN-HN (CT GDPT 2018) | ĐHSP Hà Nội / Bộ GD&ĐT | 2019 | Đặc điểm, mục tiêu, yêu cầu cần đạt, cách tổ chức hoạt động trải nghiệm-hướng nghiệp. | [Link](https://www.slideshare.net/slideshow/ti-liu-tp-hun-hng-dn-thc-hin-chng-trnh-hot-ng-tri-nghim-v-hot-ng-tri-nghim-hng-nghip/247864314) |
| 2 | Tài liệu bồi dưỡng GV — SGK HĐTN-HN 11 | NXB Giáo dục VN | 2023 | Thiết kế chủ đề, kế hoạch bài dạy, đánh giá hoạt động hướng nghiệp THPT. | [PDF](https://sachdientu.sachthietbigiaoduc.vn/upload/hdtn11/tlthbdgvsdsgkm-hdtnhn11.pdf?v=1.0.4) |
| 3 | Tập huấn SGK HĐTN-HN 8 — Cánh Diều | NXB ĐHSP | 2022 | Cấu trúc hoạt động lớp 8, tổ chức trải nghiệm, đánh giá năng lực định hướng nghề. | [PDF](https://medialib.qlgd.edu.vn/Uploads/THU_VIEN/shn/2/37/UserFiles/13.-TLTH-Hoat-dong-trai-nghiem-8-Canh-dieu-eb109b41-558b-494e-8211-47eac6a1fbd0.pdf) |
| 4 | Tập huấn GV HĐTN-HN lớp 6 | Phương Nam / ĐHSP TP.HCM | 2021 | Chuyển hóa CT GDPT 2018 → chủ đề hoạt động đầu cấp THCS. | [PDF](https://phuongnamedu.vn/media/resource/890/mRR0xnXgWyQOR.pdf) |
| 5 | Đổi mới giáo dục hướng nghiệp trong trường trung học | Bộ GD&ĐT × VVOB | 2013/14 | Thực hành đổi mới hướng nghiệp: tích hợp vào dạy học, tư vấn cá nhân, hoạt động nhà trường. | [Link](https://thuviendethi.com/tai-lieu-tap-huan-doi-moi-giao-duc-huong-nghiep-trong-truong-trung-hoc-39344/) |
| 6 | **Hướng dẫn tư vấn nghề nghiệp** (VN) | ILO Việt Nam | 2025 | ★ Quy trình & công cụ tư vấn nghề cập nhật, dùng làm chuẩn nghiệp vụ. | [Trang ILO](https://www.ilo.org/vi/resource/training-material/ilo-career-guidance-manual-viet-nam) · [PDF](https://www.ilo.org/sites/default/files/2025-06/Huong%20dan%20tu%20van%20nghe%20nghiep.pdf) |
| 7 | **Bộ sách Hướng nghiệp — Sách tra cứu nghề (bản đầy đủ)** | ILO × Bộ GD&ĐT | 2020 | ★★ "Từ điển nghề" cho HS 14–19t: nhóm nghề, yêu cầu học tập, năng lực, điều kiện làm việc, triển vọng. **Nguồn nội dung trực tiếp cho thư viện ngành/nghề (TT 16/2026 Đ.5a).** | [PDF](https://www.ilo.org/sites/default/files/wcmsp5/groups/public/%40asia/%40ro-bangkok/%40ilo-hanoi/documents/publication/wcms_756142.pdf) |
| 8 | Bộ sách Hướng nghiệp — Sổ tay tra cứu nhanh | ILO × Bộ GD&ĐT | 2020 | Bản rút gọn dùng trong lớp/​ngày hội nghề/​tư vấn nhanh. | [PDF](https://www.ilo.org/sites/default/files/wcmsp5/groups/public/%40asia/%40ro-bangkok/%40ilo-hanoi/documents/publication/wcms_756144.pdf) |
| 9 | Bộ sách Hướng nghiệp — Sách bài tập học viên | ILO × Bộ GD&ĐT | 2020 | ★ Tự khám phá sở thích/​năng lực/​giá trị nghề + thực hành ra quyết định. **Nguồn item cho module trắc nghiệm (Đ.5b) & kỹ năng chọn nghề (Đ.5c).** | [PDF](https://www.ilo.org/wcmsp5/groups/public/---asia/---ro-bangkok/---ilo-hanoi/documents/publication/wcms_756139.pdf) |
| 10 | Giáo dục Khởi nghiệp — HS THPT | ILO Việt Nam | 2019 | Bổ trợ hướng nghiệp qua tinh thần khởi nghiệp, năng lực kinh doanh. | [PDF](https://www.ilo.org/sites/default/files/wcmsp5/groups/public/%40asia/%40ro-bangkok/%40ilo-hanoi/documents/publication/wcms_712466.pdf) |
| 11 | Giáo dục Khởi nghiệp — GV THPT | ILO Việt Nam | 2019 | Thiết kế bài học khởi nghiệp liên hệ nghề nghiệp. | [PDF](https://www.ilo.org/sites/default/files/wcmsp5/groups/public/%40asia/%40ro-bangkok/%40ilo-hanoi/documents/publication/wcms_712465.pdf) |
| 12 | Hướng nghiệp cùng con thời đại 4.0 | RMIT Việt Nam | 2025 | Cẩm nang phụ huynh: đối thoại gia đình, chọn ngành/​nghề. Nguồn cho **module phụ huynh/​giám hộ**. | [PDF](https://www.rmit.edu.vn/content/dam/rmit/vn/en/assets-for-production/documents/pdfs/vn-parents-guide/vi-parent-student-career-orientation-guide-2025.pdf) |
| 13 | Cẩm nang Hướng nghiệp 2025 | ĐH Nguyễn Tất Thành | 2025 | Thông tin ngành đào tạo (kiểm tra cập nhật trước khi dùng). | [PDF](https://ntt.edu.vn/wp-content/uploads/2025/01/cam-nang-tuyen-sinh-2025.pdf) |

---

## 3. Nguồn Việt Nam — Bài báo khoa học & hướng nghiên cứu

> Dùng xây **cơ sở lý luận, khung năng lực, thang đo**. Tập trung ở *Tạp chí Khoa học Giáo dục Việt Nam* (VJES), HNUE & VNU Journals.

| # | Nguồn | Năm | Giá trị | Link |
|---|---|---|---|---|
| 1 | Khái niệm & cấu trúc năng lực tư vấn hướng nghiệp của GV THPT | 2024 | Khung năng lực tư vấn hướng nghiệp cho GV/​cố vấn. | [PDF](https://vjes.vnies.edu.vn/sites/default/files/khgdvn_-_tap_20_-_so_s1_-18-23.pdf) |
| 2 | Khung năng lực giáo dục hướng nghiệp của GV THPT | 2023 | Tiêu chí, chỉ báo, biểu hiện năng lực GV. | [PDF](https://vjes.vnies.edu.vn/sites/default/files/khgdvn_-_tap_19_-_so_08_-8-13.pdf) |
| 3 | Phát triển năng lực định hướng nghề cho HS THCS qua STEM | 2023 | Kết nối hướng nghiệp ↔ STEM, học qua dự án. | [PDF](https://vjes.vnies.edu.vn/sites/default/files/khdgvn_-_tap_19_-_so_01_-_no_08_-44-50.pdf) |
| 4 | Mô hình GD hướng nghiệp THCS vùng dân tộc thiểu số | 2023 | Công bằng giáo dục, nhóm yếu thế, bối cảnh địa phương. | [PDF](https://vjes.vnies.edu.vn/sites/default/files/khdgvn_-_tap_19_-_so_02_-_no_07-42-47.pdf) |
| 5 | GD hướng nghiệp cho nhóm trẻ rối loạn phát triển (thực trạng) | 2022 | Hướng nghiệp HS có nhu cầu đặc biệt, GD hòa nhập. | [PDF](https://vjes.vnies.edu.vn/sites/default/files/khdg_tap_18_-_so_01_nam_2022-63-67.pdf) |
| 6 | Biện pháp GD hướng nghiệp cho trẻ rối loạn phát triển | 2020 | Biện pháp thích ứng cá nhân (khuyết tật/​phổ tự kỷ). | [PDF](https://vjes.vnies.edu.vn/sites/default/files/sdb_t11-139-142.pdf) |
| 7 | Career Orientation through STEM in Chemistry | 2022 | Mẫu tích hợp hướng nghiệp vào môn học. | [VNU JS:ER](https://js.vnu.edu.vn/ER/article/view/4598/3993) |
| 8 | STEM career orientation development | 2025 | Phát triển năng lực hướng nghiệp qua dạy STEM. | [HNUE JS](https://hnuejs.edu.vn/es/article/download/511/392/4244) |
| 9 | Biến động vai trò các yếu tố hướng nghiệp trong xã hội | 1994 | Lịch sử tư tưởng hướng nghiệp VN (gia đình/​nhà trường/​xã hội). | [VNU JS:SSH](https://js.vnu.edu.vn/SSH/article/view/4173/3887) |
| 10 | Lí thuyết quản lí hoạt động tư vấn hướng nghiệp THPT | 2019 | Quản lý nhà trường: kế hoạch–tổ chức–lãnh đạo–kiểm tra. | [PDF](https://docview.dlib.vn/tvs/2020/20200610/niem/tvs_niem/40701_129001_1_pb_0544.pdf?rand=852128) |
| 11 | Kĩ năng tư vấn hướng nghiệp của GV THPT Phú Thọ | 2025 | Khảo sát thực trạng năng lực/​kỹ năng GV. | [VJES](https://vjes.vnies.edu.vn/vi/so-2-thang-02-nam-2025) |
| 12 | Quản lý hoạt động GD hướng nghiệp THCS Cần Đước, Long An | 2024 | Khảo sát thực trạng quản lý cấp THCS địa phương. | [ResearchGate](https://www.researchgate.net/publication/387665957_Thuc_trang_quan_ly_hoat_dong_giao_duc_huong_nghiep_cho_hoc_sinh_o_cac_truong_trung_hoc_co_so_huyen_Can_Duoc_tinh_Long_An) |

---

## 4. Nguồn quốc tế — Báo cáo, handbook, resource book

> Cơ sở lý luận & dữ liệu chính sách quốc tế. **ILO Resource Book** và **OECD Career Readiness** sát bối cảnh VN nhất.

| # | Nguồn | Cơ quan | Năm | Giá trị | Link |
|---|---|---|---|---|---|
| 1 | Investing in Career Guidance | OECD/ILO/UNESCO/EC/Cedefop/ETF | 2021 | ★ Tài liệu nền: lý do đầu tư hướng nghiệp, hiệu quả KT-XH, công bằng, hệ thống dịch vụ. | [UNESDOC](https://unesdoc.unesco.org/ark:/48223/pf0000378215) |
| 2 | Career Guidance and Orientation | UNESCO-UNEVOC; A.G. Watts | 2013 | Quan hệ hướng nghiệp ↔ TVET, chính sách, cấu trúc, thực hành. | [UNESDOC](https://unesdoc.unesco.org/ark:/48223/pf0000227468) |
| 3 | Handbook on Career Counselling (higher ed) | UNESCO | 2002 | Thiết kế dịch vụ tư vấn nghề ĐH: tổ chức–triển khai–đánh giá. | [UNESDOC](https://unesdoc.unesco.org/ark:/48223/pf0000125740) |
| 4 | Handbook for Career Development | ILO | 2024 | Khung phát triển nghề nghiệp thích ứng được cho chương trình GDNN & hướng nghiệp. | [ILO](https://www.ilo.org/resource/other/handbook-career-development) |
| 5 | **Career Guidance: A Resource Book for Low- & Middle-Income Countries** | ILO | 2011 | ★★ **Rất sát VN**: phát triển hệ thống hướng nghiệp, thông tin nghề, tổ chức dịch vụ, đào tạo nhân sự. | [ILO](https://www.ilo.org/publications/career-guidance-resource-book-low-and-middle-income-countries) |
| 6 | The State of Global Teenage Career Preparation | OECD | 2025 | ★ Dữ liệu PISA mới nhất về chuẩn bị nghề tuổi 15; hoạt động hiệu quả, employer engagement. | [OECD](https://www.oecd.org/en/publications/the-state-of-global-teenage-career-preparation_d5f8e3f2-en/full-report.html) |
| 7 | Career Guidance, Social Inequality and Social Mobility | OECD | 2024 | Vai trò hướng nghiệp giảm bất bình đẳng, hỗ trợ dịch chuyển xã hội. | [PDF](https://www.oecd.org/content/dam/oecd/en/publications/reports/2024/03/career-guidance-social-inequality-and-social-mobility_267a5ecd/e98d0ae7-en.pdf) |
| 8 | Career Conversations | OECD Career Readiness | 2021 | Giá trị đối thoại nghề nghiệp với HS — mô hình gia đình–nhà trường. | [PDF](https://www.oecd.org/content/dam/oecd/en/publications/reports/2021/10/career-conversations_9668eea6/15b83760-en.pdf) |
| 9 | Teenage Career Development in England | OECD | 2024 | Điển cứu hệ thống Anh: Careers Hubs, employer engagement, Gatsby. | [PDF](https://www.oecd.org/content/dam/oecd/en/publications/reports/2024/05/teenage-career-development-in-england_463c374b/13452cbe-en.pdf) |
| 10 | Lifelong Guidance across Europe | Cedefop/EU | 2011 | Khung hướng nghiệp suốt đời, liên hệ học tập suốt đời ↔ TTLĐ. | [PDF](https://www.cedefop.europa.eu/files/6111_en.pdf) |
| 11 | Lifelong Guidance Policy Development: A European Resource Kit | ELGPN | 2012 | Bộ công cụ phát triển chính sách: phối hợp liên ngành, chất lượng, dữ liệu, CMS. | [PDF](https://www.uhr.se/globalassets/syv/webbibliotek/policies-och-kvalitet/elgpn_resource_kit_2011-12_web.pdf) |
| 12 | Lifelong guidance policy & practice in the EU | Cedefop/EC; Barnes et al. | 2020 | Xu hướng, thách thức, cơ hội chính sách EU. | [PDF](https://cica.org.au/wp-content/uploads/Lifelong-guidance-policy-and-practice-in-the-EU-trends-challenges-and-opportunities.pdf) |
| 13 | European Lifelong Guidance Policies & New Skills Agenda | European Parliament | 2017 | Liên hệ hướng nghiệp ↔ kỹ năng, ESCO/EQF. | [PDF](https://www.europarl.europa.eu/RegData/etudes/BRIE/2017/595369/IPOL_BRI%282017%29595369_EN.pdf) |
| 14 | Orientation and Career Guidance Handbook | European Schools | 2024 | Mẫu tổ chức hướng nghiệp hệ thống trường đa quốc gia. | [PDF](https://www.eursc.eu/BasicTexts/Orientation_Career_guidance_handbook_2024-en.pdf) |

---

## 5. Nguồn quốc tế — Khung chuẩn, chuẩn năng lực & toolkit triển khai

> ★ Dùng thiết kế **chuẩn chương trình** (Gatsby) và **khung năng lực** người làm hướng nghiệp (NICE/NCDA/APCDA) + **năng lực đầu ra** học sinh (NACE).

| # | Nguồn | Cơ quan | Năm | Giá trị | Link |
|---|---|---|---|---|---|
| 1 | **Good Career Guidance** (gốc 8 Gatsby Benchmarks) | Gatsby; Sir John Holman | 2014 | ★★ Chuẩn tham chiếu quốc tế cho chương trình hướng nghiệp trường trung học. | [PDF](https://cica.org.au/wp-content/uploads/Gatsby-Sir-John-Holman-Good-Career-Guidance-2014.pdf) |
| 2 | Good Career Guidance: The Next 10 Years | Gatsby | 2024 | Cập nhật bằng chứng & tiêu chí đo Gatsby Benchmarks. | [PDF](https://cdn.gatsbybenchmarks.org.uk/app/uploads/2024/11/good-career-guidance-the-next-10-years-report.pdf) |
| 3 | **Gatsby Benchmark Toolkit** (Schools/​SEND) | Careers & Enterprise Company | 2025 | ★ Biến 8 chuẩn thành checklist + ví dụ + tiêu chí đo — trực tiếp dùng làm **fitness function chương trình**. | [PDF](https://resources.careersandenterprise.co.uk/sites/default/files/2025-05/1995%20-%20Gatsby%20BM%20Schools%20and%20specialist%20provision%20settings%20Toolkit%20v8.pdf) |
| 4 | NICE Handbook (đào tạo chuyên viên hướng nghiệp) | NICE Network | 2012 | Mô hình năng lực, chương trình đào tạo, chuyên nghiệp hóa nghề. | [PDF](https://www.vkotocka.si/wp-content/uploads/2018/03/Inhalt-Vollversion-NICE-Handbook-1.pdf) |
| 5 | European Competence Standards — NICE Handbook Vol. II | NICE Network | 2016 | Chuẩn tối thiểu năng lực chuyên viên — tham chiếu xây khung VN. | [PDF](https://www.euroguidance.nl/_images/user/publicaties/NICE%20Handbook%20Volume%20II%20-%20EU%20Competence%20%20Standards.pdf) |
| 6 | **Career Counseling Competencies** | NCDA | 2009+ | ★ Chuẩn năng lực nhà tư vấn nghề: đánh giá, lý thuyết, đa văn hóa, đạo đức, **công nghệ**, giám sát. | [NCDA](https://www.ncda.org/aws/NCDA/pt/sp/compentencies_career_counseling) |
| 7 | Minimum Competencies for Multicultural Career Counseling | NCDA | 2009 | Hướng nghiệp với HS đa dạng văn hóa/​dân tộc/​giới/​khuyết tật. | [PDF](https://www.counseling-csj.org/uploads/1/2/3/6/123630265/resource_ncda_multi-cultural_career_counseling_competencies_2009__2_.pdf) |
| 8 | APCDA Career Services Competencies | APCDA | 2019/23 | ★ Chuẩn **khu vực châu Á-TBD** — gần bối cảnh VN nhất. | [PDF](https://asiapacificcda.org/wp-content/uploads/2023/10/APCDA_Competencies.pdf) |
| 9 | Competencies for a Career-Ready Workforce | NACE | 2025 | ★ 8 năng lực đầu ra: career & self-development, communication, critical thinking, equity & inclusion, leadership, professionalism, teamwork, technology. | [PDF](https://www.naceweb.org/docs/default-source/default-document-library/2025/career-readiness/competencies/nace-career-readiness-competencies-december-2025.pdf?sfvrsn=a8abf91a_3) |

---

## 6. Giáo trình, chuyên khảo nền tảng (lý thuyết phát triển nghề nghiệp)

| # | Nguồn | Tác giả/NXB | Năm | Giá trị | Link |
|---|---|---|---|---|---|
| 1 | Career Development and Counseling: Putting Theory and Research to Work | Brown & Lent, Wiley | 2013/20 | ★ Giáo trình mạnh về lý thuyết phát triển nghề + can thiệp tư vấn. | [Wiley](https://www.wiley.com/en-us/Career+Development+and+Counseling%3A+Putting+Theory+and+Research+to+Work%2C+3rd+Edition-p-9781119580352) |
| 2 | Career Counseling: A Holistic Approach | Vernon G. Zunker | 2016 | Đánh giá, lý thuyết, quy trình tư vấn, các nhóm thân chủ. | [Cengage](https://www.cengage.com/c/career-counseling-a-holistic-approach-9e-zunker/) |
| 3 | Career Counseling: Foundations, Perspectives, and Applications | Capuzzi & Stauffer | 2019 | Nền tảng + ứng dụng + bối cảnh thực hành hiện đại. | [Routledge](https://www.routledge.com/Career-Counseling-Foundations-Perspectives-and-Applications/Capuzzi-Stauffer/p/book/9781138743554) |
| 4 | Career Theory and Practice: Learning Through Case Studies | Swanson & Fouad | 2019 | Học lý thuyết qua ca tư vấn. | [SAGE](https://us.sagepub.com/en-us/nam/career-theory-and-practice/book257016) |
| 5 | Career Counseling and Development in a Global Economy | Andersen & Vandehey | 2012 | Toàn cầu hóa ↔ thay đổi TTLĐ ↔ tư vấn nghề. | [Cengage](https://www.cengage.com/c/career-counseling-and-development-in-a-global-economy-2e-andersen-vandehey/) |
| 6 | International Handbook of Career Guidance | Athanasou & Van Esbroeck, Springer | 2008/19 | Bao quát lịch sử, chính sách, thực hành, đánh giá, nghiên cứu. | [Springer](https://link.springer.com/book/10.1007/978-1-4020-6230-8) |
| 7 | Handbook of Career Development: International Perspectives | Arulmani et al., Springer | 2014 | ★ Góc nhìn đa văn hóa — hữu ích khi **bản địa hóa** mô hình cho VN. | [Springer](https://link.springer.com/book/10.1007/978-1-4614-9460-7) |
| 8 | Handbook of Vocational Psychology | Walsh, Savickas & Hartung | 2013 | Nền tâm lý học nghề: lựa chọn nghề, thích ứng nghề, bản sắc nghề. | [Routledge](https://www.routledge.com/Handbook-of-Vocational-Psychology-Theory-Research-and-Practice/Walsh-Savickas-Hartung/p/book/9780415805404) |

---

## 7. Tạp chí khoa học cần theo dõi định kỳ

| # | Tạp chí | NXB/Cơ quan | Phạm vi |
|---|---|---|---|
| 1 | [International Journal for Educational and Vocational Guidance](https://link.springer.com/journal/10775) | Springer/IAEVG | ★ Sát nhất: giáo dục hướng nghiệp, tư vấn nghề, chính sách so sánh. |
| 2 | [Journal of Career Development](https://journals.sagepub.com/home/jcd) | SAGE | Lý thuyết, nghiên cứu, thực hành phát triển nghề. |
| 3 | [The Career Development Quarterly](https://www.ncda.org/aws/NCDA/pt/sp/cdquarterly) | Wiley/NCDA | Can thiệp tư vấn nghề, coaching, quản lý nghề. |
| 4 | [Journal of Vocational Behavior](https://www.sciencedirect.com/journal/journal-of-vocational-behavior) | Elsevier | Lựa chọn nghề, thích ứng công việc, chuyển tiếp nghề. |
| 5 | [British Journal of Guidance & Counselling](https://www.tandfonline.com/journals/cbjg20) | Taylor & Francis | School counselling/​career guidance. |
| 6 | [Australian Journal of Career Development](https://journals.sagepub.com/home/acd) | SAGE/CICA | ★ Gần bối cảnh châu Á-TBD. |
| 7 | [Tạp chí Khoa học Giáo dục Việt Nam (VJES)](https://vjes.vnies.edu.vn/) | Viện KHGD VN | ★ Nguồn VN quan trọng nhất. |
| 8 | [Tạp chí Giáo dục](https://tapchigiaoduc.moet.gov.vn/) | Bộ GD&ĐT | Tích hợp hướng nghiệp trong môn học, HĐTN, quản lý GD. |
| 9 | [HNUE Journal of Science: Educational Sciences](https://hnuejs.edu.vn/es) | ĐHSP Hà Nội | Tâm lý–giáo dục, HĐTN, GD đặc biệt, STEM. |
| 10 | [VNU Journal of Science: Education Research](https://js.vnu.edu.vn/ER) | ĐHQGHN | GD, STEM, định hướng nghề, chính sách đào tạo. |

---

## 8. Cổng nguồn & tổ chức theo dõi dài hạn

| # | Nguồn | Cơ quan | Dùng để |
|---|---|---|---|
| 1 | [Cổng Bộ GD&ĐT](https://moet.gov.vn/) | Bộ GD&ĐT | Văn bản, chương trình, tài liệu tập huấn, tin chính sách. |
| 2 | [CSDL văn bản Chính phủ](https://vanban.chinhphu.vn/) | VPCP | ★ Kiểm tra **hiệu lực** VBPL — ưu tiên trước khi trích dẫn. |
| 3 | [ILO Việt Nam](https://www.ilo.org/vi/regions-and-countries/asia-and-pacific/viet-nam) | ILO | Tài liệu hướng nghiệp, khởi nghiệp, TTLĐ, việc làm bền vững. |
| 4 | [OECD Education](https://www.oecd.org/education/) | OECD | Dữ liệu PISA, bằng chứng hoạt động hướng nghiệp ↔ kết quả việc làm. |
| 5 | [UNESCO Digital Library](https://unesdoc.unesco.org/) | UNESCO | Báo cáo UNESCO/UNEVOC về TVET, career guidance, lifelong learning. |
| 6 | [Cedefop](https://www.cedefop.europa.eu/) | EU | Chính sách & công cụ hướng nghiệp suốt đời, GDNN châu Âu. |
| 7 | [Careers & Enterprise Company](https://resources.careersandenterprise.co.uk/) | CEC UK | ★ Toolkit theo Gatsby, employer engagement, đánh giá chương trình. |
| 8 | [NCDA](https://www.ncda.org/) | NCDA | Chuẩn năng lực, đạo đức, tài liệu chuyên môn. |
| 9 | [APCDA](https://asiapacificcda.org/) | APCDA | Năng lực nghề + mạng lưới chuyên gia châu Á-TBD. |
| 10 | [ERIC](https://eric.ed.gov/) | IES, US | CSDL học thuật: career education/​guidance/​school counseling. |

---

## 9. Bản đồ nguồn → Module WeUp Career (value-add)

> Khớp nguồn tri thức với 5 nội dung cốt lõi **TT 16/2026 Điều 5** (xem [`legal-basis.md` §4.5](../legal/legal-basis.md)) để mỗi module vừa có **căn cứ pháp lý** vừa có **nền nội dung/​khoa học**.

| Module (Điều 5) | Nguồn pháp lý/​nội dung VN | Nguồn lý luận/​chuẩn quốc tế |
|---|---|---|
| **(a) Thông tin nghề nghiệp** — thư viện ngành/nghề | ILO "Sách tra cứu nghề" 2020 (§2.7), CT GDPT (§1.4), TTLĐ (Luật 74/2025) | ISCO/O*NET; ILO Resource Book (§4.5) |
| **(b) Trắc nghiệm tự nhận thức** (RIASEC/MBTI) — *dữ liệu nhạy cảm* | ILO Sách bài tập (§2.9), HĐTN-HN | Holland/RIASEC; Super; Handbook of Vocational Psychology (§6.8) |
| **(c) Kỹ năng lựa chọn nghề & ra quyết định** | ILO Hướng dẫn tư vấn 2025 (§2.6), TT 07/2022 | Career Management Skills (ELGPN §4.11); SCCT; Krumboltz |
| **(d) Trải nghiệm nghề nghiệp** | HĐTN-HN (§1.4), Đề án 522 mô hình (§1.7) | Gatsby BM 5–6 (§5.1–5.3); OECD employer engagement (§4.9) |
| **(đ) Nền tảng số / chuyển đổi số** | TT 16/2026 Đ.5đ, NQ 71, QĐ 1705 NV8 | NCDA "technology" competency (§5.6); đạo đức AI (câu hỏi NC §12) |
| **Khung năng lực người tư vấn** (counselor) | TT 18/2025 (§1.2), VJES năng lực GV (§3.1–3.2) | NICE (§5.4–5.5), NCDA (§5.6), APCDA (§5.8) |
| **Đo lường & chất lượng chương trình** | QĐ 525 (100% HS đến 2030) | Gatsby Toolkit (§5.3) → fitness functions; OECD State of Teenage (§4.6) |
| **Công bằng & hòa nhập** | VJES dân tộc thiểu số/​trẻ đặc biệt (§3.4–3.6) | OECD Social Mobility (§4.7); NCDA multicultural (§5.7) |

---

## 10. Lộ trình đọc cho team nghiên cứu

1. **GĐ1 — Nắm khung VN:** TT 16/2026 → TT 18/2025 → CT GDPT tổng thể → CT HĐTN-HN. *Mục tiêu:* "hướng nghiệp" trong trường VN gồm gì, ai làm, điều kiện gì, quan hệ với phân luồng.
2. **GĐ2 — Hiểu hoạt động trong trường:** tài liệu tập huấn HĐTN-HN + bộ ILO Việt Nam. *Mục tiêu:* chính sách → hoạt động/​chủ đề/​công cụ/​cẩm nang nghề.
3. **GĐ3 — Xây cơ sở lý luận:** ILO Resource Book → UNESCO Career Guidance → OECD Career Readiness → NICE → NCDA. *Mục tiêu:* khung lý thuyết, chuẩn năng lực, mô hình dịch vụ, tiêu chí chất lượng.
4. **GĐ4 — Xây mô hình triển khai:** Gatsby Good Career Guidance + Toolkit 2025 → OECD England → Cedefop/ELGPN. *Mục tiêu:* chuẩn chương trình cấp trường, employer engagement, dữ liệu đo lường.
5. **GĐ5 — Viết tổng quan nghiên cứu:** IJEVG, J. Career Development, J. Vocational Behavior, Career Development Quarterly, VJES, HNUE, VNU JS:ER.

---

## 11. Bộ từ khóa tìm kiếm

- **Tiếng Việt:** hướng nghiệp; giáo dục hướng nghiệp; tư vấn hướng nghiệp; định hướng nghề nghiệp; phân luồng học sinh; hoạt động trải nghiệm hướng nghiệp; năng lực định hướng nghề nghiệp; kỹ năng tư vấn hướng nghiệp; quản lý hoạt động hướng nghiệp; giáo dục STEM và hướng nghiệp; thông tin thị trường lao động; tư vấn học đường.
- **Tiếng Anh:** career guidance; career education; career counselling; career development; vocational guidance; career readiness; career management skills; career decision-making; school career guidance; employer engagement; lifelong guidance; transition from school to work; labour market information; career guidance policy; career guidance competencies.
- **Cú pháp:** `site:moet.gov.vn "hướng nghiệp" pdf` · `site:ilo.org Vietnam "hướng nghiệp"` · `site:vjes.vnies.edu.vn "hướng nghiệp"` · `"career guidance" "OECD" pdf` · `"career guidance" "UNESCO" pdf` · `"Gatsby Benchmarks" toolkit pdf`.

---

## 12. Câu hỏi nghiên cứu định hướng sản phẩm

1. Mô hình **năng lực hướng nghiệp của học sinh VN** gồm thành tố nào: tự nhận thức, hiểu nghề, hiểu TTLĐ, ra quyết định, lập kế hoạch học tập–nghề nghiệp, thích ứng chuyển tiếp? → định hình **schema `assessment` & `profile`**.
2. **Khung năng lực GV/​chuyên viên tư vấn** trong trường VN dựa chuẩn nào: NCDA, NICE, APCDA hay bản địa? → định hình **vai trò `counselor`**.
3. Chương trình hướng nghiệp cấp trường **đo bằng chỉ báo nào**: số hoạt động, chất lượng tư vấn, mức cá nhân hóa, employer engagement, dữ liệu đầu ra, công bằng tiếp cận? → **analytics & fitness functions**.
4. Tích hợp hướng nghiệp vào HĐTN-HN, môn STEM, tư vấn học đường, hoạt động phụ huynh ra sao? → **content model & module phụ huynh**.
5. Dữ liệu TTLĐ, CSDL nghề và công cụ số/​AI dùng thế nào để hỗ trợ HS **vẫn bảo đảm đạo đức, bảo mật, tránh định kiến thuật toán**? → ràng buộc **Khối C ([`legal-basis.md`](../legal/legal-basis.md)) + minh bạch thuật toán**.

---

## 13. Danh mục 20 nguồn nên đọc trước

1. TT 16/2026/TT-BGDĐT — hướng nghiệp & phân luồng. *(§1.1)*
2. ⛔ QĐ 522/QĐ-TTg 2018 — Đề án hướng nghiệp & phân luồng *(tham chiếu mô hình, §1.7)*.
3. CT GDPT 2018 — Chương trình tổng thể. *(§1.3)*
4. CT GDPT 2018 — HĐTN-HN. *(§1.4)*
5. TT 18/2025/TT-BGDĐT — tư vấn học đường & công tác xã hội. *(§1.2)*
6. ILO VN — Sách tra cứu nghề. *(§2.7)*
7. ILO VN — Sách bài tập hướng nghiệp. *(§2.9)*
8. ILO VN — Hướng dẫn tư vấn nghề nghiệp 2025. *(§2.6)*
9. ILO — Resource Book for Low/Middle-Income Countries. *(§4.5)*
10. ILO — Handbook for Career Development 2024. *(§4.4)*
11. UNESCO-UNEVOC — Career Guidance and Orientation. *(§4.2)*
12. UNESCO — Handbook on Career Counselling. *(§4.3)*
13. OECD — State of Global Teenage Career Preparation 2025. *(§4.6)*
14. OECD — Career Guidance, Social Inequality and Social Mobility 2024. *(§4.7)*
15. Gatsby — Good Career Guidance 2014. *(§5.1)*
16. Gatsby — Good Career Guidance: The Next 10 Years 2024. *(§5.2)*
17. CEC — Gatsby Benchmark Toolkit 2025. *(§5.3)*
18. NICE Handbook — đào tạo chuyên viên hướng nghiệp. *(§5.4)*
19. NCDA — Career Counseling Competencies. *(§5.6)*
20. VJES — bài về năng lực giáo dục/​tư vấn hướng nghiệp của GV. *(§3.1–3.2)*

---

## 14. Thực trạng hướng nghiệp Việt Nam — số liệu thực chứng (design rationale & KPI)

> Nguồn: `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md` (Phần III, VI, VII — tổng hợp từ ~44 nguồn ở Phụ lục D của tài liệu đó: GSO, Tạp chí Giáo dục, Tạp chí Toà án, khảo sát báo chí giáo dục). **Đây là "vì sao xây WeUp Career" và là baseline để đặt KPI/​OKR sản phẩm** — không phải VBPL, nên đặt ở thư viện tri thức nền này thay vì `legal-basis.md`.

| # | Chỉ số thực trạng (pain point) | Hệ quả thiết kế / KPI mục tiêu |
|---|---|---|
| 1 | **~63% HS THPT chưa xác định được nghề** muốn theo | Module (b) trắc nghiệm + (a) thông tin nghề là lõi MVP; KPI: % người dùng hoàn tất hồ sơ định hướng. |
| 2 | **~70% SV chưa từng được hướng nghiệp đầy đủ**; chỉ **~30% trường THPT có chương trình bài bản** | Khoảng trống dịch vụ lớn ⇒ cơ hội thị trường; chuẩn hóa nội dung theo TT 16/2026 Đ.5. |
| 3 | **~60% SV chọn sai ngành** (khảo sát TP.HCM); **>40% chọn sai ngành sau nhập học**; chỉ **~56% làm đúng ngành** đào tạo | KPI tác động dài hạn: giảm tỉ lệ hối tiếc chọn ngành; cần theo dõi cohort theo thời gian (longitudinal). |
| 4 | **~30% bỏ ĐH → CĐ/TC mỗi năm**; **~10% bị thôi học** | Chi phí xã hội của hướng nghiệp kém ⇒ luận cứ ROI cho nhà nước/​nhà đầu tư. |
| 5 | **Phân luồng sau THCS chỉ 17,8–21%** (mục tiêu Đề án 522 cũ = 40%); **74,5% HS THCS vào THPT** | Gợi ý phân luồng **không ép buộc** (TT 16/2026 + Luật 123/2025); mô hình hóa "trường trung học nghề" (Luật GDNN 124/2025) như một nhánh. |
| 6 | **68,52% trường THCS** có hướng nghiệp gắn thực tiễn (cao hơn THPT) | Ưu tiên cấp THCS cho tính năng trải nghiệm nghề (d); nội dung versioned theo `school_level`. |

**Cách dùng:** (1) trích làm phần "Bối cảnh & vấn đề" trong `spec.md`/​pitch; (2) chuyển thành **baseline KPI** đo tác động sản phẩm; (3) **kiểm tra cập nhật** từng số liệu trước khi công bố (nhiều số là khảo sát vùng/​năm cụ thể — xem Phụ lục D của tài liệu nguồn để truy nguồn gốc).

---

## 15. Mô hình quốc tế tham chiếu sâu — Singapore (benchmark tính năng)

> Nguồn: `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md` Phần IX (bài học Singapore). Singapore là benchmark gần bối cảnh châu Á nhất cho **một hệ thống hướng nghiệp quốc gia có cổng số tập trung** — ánh xạ trực tiếp tới tầm nhìn WeUp Career.

| # | Mô hình Singapore | Mô tả | Ánh xạ tính năng WeUp Career |
|---|---|---|---|
| 1 | **ECG Developmental Model** (Education & Career Guidance) | Hướng nghiệp **liên tục** từ tiểu học → trưởng thành, theo giai đoạn phát triển. | Khung nội dung phân tầng theo `school_level` + tính **liên tục hồ sơ** suốt vòng đời người dùng. |
| 2 | **ECG Counsellor** (MOE bổ nhiệm, 1 chuyên viên / 2–5 trường) | Đội ngũ tư vấn chuyên trách, chuẩn hóa. | Vai trò `counselor` (B2B2C); định mức & quy trình tham chiếu khi thiết kế module trường học. |
| 3 | **MySkillsFuture** (cổng quốc gia) | Một cổng số quốc gia: thông tin nghề + trắc nghiệm + lộ trình kỹ năng + tài khoản học tập suốt đời. | ★ **Bản thiết kế tham chiếu trực tiếp cho WeUp Career** — cổng quốc gia tích hợp đa persona (HS → người đi làm). |
| 4 | **V.I.P.S. assessment** (Values–Interests–Personality–Skills) | Bộ trắc nghiệm 4 trục chuẩn hóa quốc gia. | Khung **schema `assessment`**: bổ sung trục Giá trị (Values) bên cạnh RIASEC/MBTI; tránh phụ thuộc một thang đo. |
| 5 | **SWAP — "Tuần trải nghiệm nghề"** (5 ngày: Logbook + mentor + Sharing Session) | Trải nghiệm nghề có cấu trúc, có nhật ký & phản hồi. | Module (d) trải nghiệm nghề: mô hình **logbook + mentor + buổi chia sẻ**; kết nối doanh nghiệp giai đoạn sau. |
| 6 | **"Journeying with Our Children"** (cẩm nang phụ huynh) | Sổ tay đồng hành cùng con chọn nghề. | **Module phụ huynh/​giám hộ** (cũng khớp ràng buộc giám hộ < 16t ở Khối C); nội dung tham chiếu RMIT §2.12. |
| 7 | **Electronic portfolio** (theo HS lớp 6 → trưởng thành) | Hồ sơ điện tử tích lũy liên tục qua các cấp. | **`profile`/​`portfolio`** bền vững, kế thừa qua cấp học — quyết định data model phải hỗ trợ vòng đời dài + xuất/​nhập dữ liệu. |

**Cảnh báo bản địa hóa:** Singapore có MOE tập trung mạnh + quy mô nhỏ; VN phân cấp & đa dạng vùng miền hơn ⇒ tham chiếu **mô hình**, không sao chép định mức. Bản địa hóa qua nguồn §6.7 (Handbook of Career Development: International Perspectives) + §5.8 (APCDA châu Á-TBD).

---

## 16. Nút thắt hệ thống & 6 đề xuất chiến lược (design drivers)

> Nguồn: `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md` Phần IX. **4 nút thắt** giải thích vì sao hướng nghiệp VN kém hiệu quả; **6 đề xuất** là không gian cơ hội — trong đó **đề xuất #3 = "Cổng quốc gia Hướng nghiệp Việt Nam" chính là sứ mệnh WeUp Career.**

**4 nút thắt (bottlenecks):**
1. **Nhân sự** — thiếu chuyên viên tư vấn hướng nghiệp chuyên trách, GV kiêm nhiệm thiếu năng lực (đối chiếu khung năng lực §5.4–5.8). ⇒ Sản phẩm phải **hỗ trợ/​khuếch đại GV kiêm nhiệm**, không giả định có chuyên gia.
2. **Văn hóa** — tâm lý chuộng bằng cấp, định kiến nghề "thấp/​cao". ⇒ Nội dung phải **giải định kiến nghề**, đề cao GDNN & trường trung học nghề (Luật 124/2025).
3. **Hạ tầng** — **không có cổng quốc gia + không có bộ trắc nghiệm chuẩn hóa quốc gia**. ⇒ Đây là khoảng trống WeUp Career lấp; cần V.I.P.S.-style assessment chuẩn hóa (§15.4).
4. **Liên kết** — rời rạc giữa nhà trường ↔ doanh nghiệp ↔ gia đình ↔ cơ sở GDNN. ⇒ Kiến trúc đa-persona + adapter dữ liệu TTLĐ (Luật Việc làm 74/2025) + module phụ huynh + kênh trường.

**6 đề xuất chiến lược (opportunity space):**
1. Chuẩn hóa **khung năng lực & đào tạo** chuyên viên hướng nghiệp → căn cứ vai trò `counselor`.
2. Đưa hướng nghiệp **xuyên suốt & sớm** (từ THCS) → khớp TT 16/2026 (xuyên suốt) + Luật GDNN 124/2025 (trường trung học nghề sau THCS).
3. **★ Cổng quốc gia Hướng nghiệp Việt Nam** — *chính là WeUp Career*: thông tin nghề + trắc nghiệm chuẩn + lộ trình + dữ liệu TTLĐ, đa persona. **Đây là tuyên ngôn sứ mệnh sản phẩm.**
4. **Bộ trắc nghiệm chuẩn hóa quốc gia** (kiểu V.I.P.S.) → module (b), khung `assessment`.
5. **Gắn kết doanh nghiệp & trải nghiệm thực tế** (kiểu SWAP) → module (d).
6. **Đồng hành cùng gia đình** (kiểu "Journeying with Our Children") → module phụ huynh/​giám hộ.

**Cách dùng:** mỗi đề xuất ↔ một nhóm tính năng có truy vết tới (a) pain point §14, (b) căn cứ pháp lý `legal-basis.md`, (c) mô hình tham chiếu §15 ⇒ dùng làm **xương sống "problem → feature → evidence"** khi viết `spec.md` và pitch.
