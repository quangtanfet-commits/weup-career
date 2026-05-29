# Phân tích chuyên sâu & hợp nhất 3 framework hướng nghiệp quốc tế — WeUp Career

> **Mục đích:** Biến 3 framework tham chiếu — **NCDG (Hoa Kỳ)**, **ABCD (Úc)**, **ECG (Singapore)** — thành **căn cứ thiết kế sản phẩm** cho WeUp Career: một mô hình năng lực + mô hình phát triển + bộ công cụ đánh giá có thể đưa thẳng vào data model và tính năng.
>
> **Ngày lập:** 2026-05-29 · **Nguồn gốc:** mổ xẻ từ `docs/temp/Framework_NCDG_NCDA_HuongNghiep.md`, `docs/temp/Framework_ABCD_CICA_HuongNghiep.md`, `docs/temp/Framework_ECG_Singapore_HuongNghiep.md`.
> **Quan hệ tài liệu:** Ràng buộc pháp lý ở [`docs/legal/legal-basis.md`](../legal/legal-basis.md) (đặc biệt §4.5 — TT 16/2026 Điều 5, và §6 BVDLCN). Thư viện nguồn nền ở [`sources.md`](./sources.md). Tài liệu này là **lớp lý luận–thiết kế** nối hai tài liệu đó với data model & tính năng.
>
> ⚠️ Ba tài liệu gốc trong `docs/temp/` đã tóm tắt rất tốt **nội dung** từng framework. Tài liệu này **không tóm tắt lại** — nó phân tích **cấu trúc/“hình dạng”** từng framework, lý do thiết kế, điểm dùng được & không dùng được cho **một sản phẩm phần mềm**, rồi hợp nhất.

---

## 0. Tóm tắt điều hành (đọc cái này trước)

Ba framework **không phải ba phiên bản của cùng một thứ**. Chúng nằm ở **ba lớp thiết kế khác nhau**, trả lời ba câu hỏi khác nhau:

| Framework | Câu hỏi nó trả lời | Bản chất | Vai trò trong WeUp Career |
|---|---|---|---|
| **NCDG (Mỹ)** | *“Làm sao **đo** được mức thuần thục?”* | Bản thể luận **đo lường** (competency → indicator → giai đoạn Bloom K/A/R + hệ mã hóa) | **Xương sống đo tiến bộ & gắn thẻ nội dung** |
| **ABCD (Úc)** | *“Cần những **năng lực** nào suốt đời?”* | Bản thể luận **phát triển–năng lực** (3 lĩnh vực → 12 năng lực → 5 giai đoạn **phi tuyến, không gắn tuổi**) | **Cây năng lực dễ đọc + trục suốt-đời cho người đi làm + sức khỏe tinh thần** |
| **ECG (Singapore)** | *“Làm sao **triển khai & thể chế hóa**?”* | Bản thể luận **hệ thống/phân phối** (3 mục tiêu → 3 giai đoạn **gắn cấp lớp** → VIPS+RIASEC → portal + tư vấn 3 tầng + phụ huynh + SkillsFuture suốt đời) | **Bộ khung hệ thống, lộ trình theo cấp lớp, mô hình vai trò, bản thiết kế portal số** |

**Khuyến nghị quyết định (không phải “chọn 1 trong 3” — mà **xếp lớp**):**

1. **Lấy ECG làm bộ xương hệ thống & lộ trình theo cấp lớp** — vì nó *là* bản thiết kế của một nền tảng hướng nghiệp quốc gia có portal, và 3 giai đoạn gắn cấp lớp khớp trực tiếp với cấu trúc lớp học VN + “yêu cầu cần đạt theo cấp” của CTGDPT 2018.
2. **Lấy 12 năng lực ABCD làm từ vựng cây năng lực** (human-readable), **cộng tính phi tuyến của ABCD làm lớp phủ cho người đi làm** (`user_type = working`), **và năng lực “Sức khỏe tinh thần & thể chất” (NL4, mới 2022)** — khớp mạnh với bối cảnh tư vấn học đường VN (TT 18/2025).
3. **Lấy hệ mã hóa & chỉ báo K-A-R của NCDG làm lớp đo lường** — đây là thứ duy nhất trong ba framework cho phép phần mềm **theo dõi tiến bộ** và **đánh giá** một cách định lượng (tính năng cốt lõi của một sản phẩm số).
4. **Lấy VIPS (Singapore) + RIASEC (cả ba dùng) làm bộ công cụ tự đánh giá** — ánh xạ thẳng vào item của **Sách bài tập học viên ILO Việt Nam** đã có trong [`sources.md`](./sources.md) §2.

**Đóng góp trung tâm của tài liệu này** là chỉ ra: ba framework dùng **hai trục khác nhau bị nhầm là một** (xem §3). WeUp Career cần mô hình hóa **2 trục trực giao**: *trục giai đoạn phát triển* (người học đang ở đâu trong hành trình) và *trục độ sâu nhận thức K-A-R* (đã thuần thục năng lực đến đâu). Đây là chìa khóa để vừa bám CTGDPT 2018 vừa đo được tiến bộ.

---

## 1. Mổ xẻ từng framework theo góc nhìn “xây sản phẩm”

### 1.1. NCDG (Mỹ, NCDA 2024) — *bản thể luận đo lường*

**Hình dạng:** `Domain (3) → Goal (11) → Indicator of Mastery (nhiều) → 3 giai đoạn học tập K-A-R`, có **hệ mã hóa** `SEL1.K2`, `CD2.A4`, `ALL1.R3`.

- 3 lĩnh vực: **CD** (Phát triển nghề nghiệp, 5 mục tiêu), **ALL** (Học tập học thuật & suốt đời, 2 mục tiêu), **SEL** (Học tập cảm xúc–xã hội, 4 mục tiêu).
- Mỗi chỉ báo được phát biểu ở **3 độ sâu Bloom**: **K** (Knowledge Acquisition — nhận biết/mô tả), **A** (Application — thực hành/chứng minh), **R** (Reflection — phân tích/đánh giá/điều chỉnh).

**Điểm thiên tài (cho phần mềm):** *tính đo được*. Mỗi chỉ báo là một **mệnh đề kiểm chứng được** ở 3 mức. Hệ mã hóa cho phép gắn thẻ từng bài học/câu trắc nghiệm/hoạt động vào một toạ độ chính xác và **theo dõi người học leo từ K→A→R**. Không framework nào khác có thuộc tính này.

**Điểm yếu (cho phần mềm):**
- **Không có giàn giáo tuổi/cấp lớp** — K-A-R là độ sâu *nhận thức*, không nói “lớp 8 nên học gì”. Tự thân NCDG không xếp lộ trình theo cấp học.
- **Không có công cụ đánh giá** (không kèm RIASEC/VIPS) — nó là *chuẩn checklist*, không phải bộ test.
- **Bùng nổ số chỉ báo & đặc thù Mỹ:** riêng CD2 có 9 nhóm × 3 = 27 mệnh đề; SEL2 có 11 × 3 = 33. Nhập nguyên si sẽ phình nội dung và lệch ngữ cảnh (vd “di chuyển địa lý”, “tự kinh doanh” theo nghĩa Mỹ).

**Dùng gì:** lấy **phương pháp mã hóa + mô hình 3 độ sâu K-A-R** làm *lớp đo lường*; **không** bê nguyên hàng trăm chỉ báo. Tuyển một tập con chỉ báo, ánh xạ vào Điều 5 + item ILO VN.

> **Cầu nối VN quan trọng:** chính tài liệu NCDG ghi nhận K-A-R ≈ **Nhận biết → Thực hiện → Vận dụng** của CTGDPT 2018. Đây là điểm khớp pedagogical để dùng K-A-R mà vẫn “nói tiếng Việt giáo dục”.

### 1.2. ABCD (Úc, CICA 2022) — *bản thể luận phát triển–năng lực*

**Hình dạng:** `Learning Area (3) → Competency (12) → 5 Career Phases`, mỗi ô = **1 phát biểu/giai đoạn/năng lực** (đã đơn giản hóa từ Ấn bản 1).

- 3 lĩnh vực: **A. Quản lý bản thân** (NL1–4), **B. Khám phá học tập & công việc** (NL5–8), **C. Xây dựng nghề nghiệp** (NL9–12).
- 5 giai đoạn: **Awareness → Exploring → Starting Out → Groundwork → Advancing**, **phi tuyến** và **không gắn tuổi**.

**Điểm thiên tài (cho phần mềm):**
- **Tính phi tuyến suốt đời.** Một người có thể “Advancing” ở lĩnh vực này nhưng “Awareness” ở lĩnh vực mới. → **Đây chính là mô hình cho người đi làm** (`user_type = working`): chuyển nghề = quay lại Awareness/Exploring trong một domain mới. Không có cái này thì segment “người đi làm” của WeUp không có chỗ dựa lý thuyết.
- **Năng lực 4 “Quản lý sức khỏe tinh thần & thể chất” (mới 2022).** Trùng khít bối cảnh tâm lý học đường VN và **TT 18/2025** (tư vấn học đường). Là điểm khác biệt đáng tích hợp tường minh.
- **12 năng lực là từ vựng người-đọc-được** — đặt tên cây năng lực dễ hiểu cho học sinh/phụ huynh/giáo viên hơn là mã NCDG.

**Điểm yếu:** **quá thô để đo** — chỉ 1 phát biểu/ô (60 ô = 12×5). Đủ để mô tả lộ trình, **không đủ để chấm điểm tiến bộ**. Phải mượn lớp đo của NCDG.

**Dùng gì:** **12 năng lực × 3 lĩnh vực = cây năng lực gốc**; **5 giai đoạn phi tuyến = lớp phủ cho người đi làm**; **NL4 = module sức khỏe tinh thần tường minh**.

### 1.3. ECG (Singapore, MOE/SSG 2024) — *bản thể luận hệ thống/phân phối*

**Hình dạng:** `3 ECG Goals (câu hỏi dẫn) → 3 giai đoạn gắn cấp lớp → nội dung VIPS + RIASEC → hệ sinh thái phân phối`.

- 3 mục tiêu = 3 câu hỏi: **Discovering Purpose (Tôi là ai?) → Exploring Opportunities (Tôi muốn đi đâu?) → Staying Relevant (Tôi đến đó bằng cách nào?)**.
- 3 giai đoạn **gắn cấp lớp**: **Awareness** (Tiểu học) → **Exploration** (THCS) → **Planning** (Dự bị ĐH/CĐ). Nguyên tắc: ở cấp nào cũng có cả ba, chỉ khác **trọng số nhấn mạnh** (lớp 8 = Exploration nhưng vẫn tiếp tục Awareness và chớm Planning).
- Nội dung lõi: **VIPS** (Values–Interests–Personality–Skills) làm bộ tự nhận thức; **RIASEC** (Holland) làm chuẩn đánh giá sở thích (triển khai ~Sec 2 ≈ lớp 8).
- Hệ sinh thái: **MySkillsFuture portal** (phân tầng theo cấp), **ECG Counsellors** + **mô hình hỗ trợ 3 tầng** (Tier 1 đại trà / Tier 2 nhóm mục tiêu / Tier 3 cá nhân), **phụ huynh tham gia** (VIPS conversations), **SkillsFuture** = ECG suốt đời cho người lớn (credit, work-study, career coaches).

**Điểm thiên tài (cho phần mềm):** ECG **gần như chính là bản thiết kế của WeUp Career**. Nó tích hợp bắt buộc vào chương trình (CCE), có **portal số phân tầng**, có **mô hình vai trò** (counsellor/giáo viên/phụ huynh/học sinh), và có **lớp suốt đời** (SkillsFuture) cho người đi làm. 3 giai đoạn gắn cấp lớp khớp trực tiếp với cấu trúc lớp VN và lối “yêu cầu cần đạt theo cấp” của CTGDPT 2018.

**Điểm yếu:** **cấu trúc năng lực/chỉ báo không mịn bằng NCDG** (3 mục tiêu là câu hỏi dẫn, không phải thang đo); **thể chế hóa nặng đặc thù Singapore** (PSLE, JC, ITE, EAE, Earn & Learn) — lấy *mẫu hình*, không lấy *định chế*.

**Dùng gì:** **3 giai đoạn gắn cấp lớp = trục phát triển chính cho học sinh**; **3 câu hỏi = khung UX/onboarding**; **VIPS+RIASEC = bộ test**; **portal + 3 tầng + phụ huynh + SkillsFuture = kiến trúc tính năng & vai trò**.

---

## 2. So sánh trên các trục **liên quan đến việc xây dựng** (khác bảng so sánh trong tài liệu gốc)

Bảng so sánh trong tài liệu gốc (NCDG §7 / ECG §7) so trên trục *chính sách/giáo dục*. Bảng dưới so trên trục **kỹ thuật–sản phẩm**:

| Trục thiết kế | NCDG (Mỹ) | ABCD (Úc) | ECG (Singapore) | Hệ quả cho WeUp |
|---|---|---|---|---|
| **Độ mịn đo lường** | ★★★ Cao (indicator × K-A-R, mã hóa) | ★ Thấp (1 phát biểu/ô) | ★★ Trung bình (outcome-level) | → đo lường **theo NCDG** |
| **Gắn cấp lớp/tuổi** | Không (phi tuổi) | Không (phi tuổi, phi tuyến) | ★★★ Có (theo cấp học) | → staging **theo ECG** |
| **Phủ người đi làm/suốt đời** | Có (phi tuổi) | ★★★ Mạnh (phi tuyến) | ★★★ Mạnh (SkillsFuture) | → người-đi-làm = **ABCD phi tuyến + SkillsFuture** |
| **Bộ công cụ tự đánh giá** | Không kèm | Không kèm | ★★★ VIPS + RIASEC | → instrument **theo ECG** |
| **Mô hình phân phối/vai trò** | Counselor (không cấu trúc cứng) | Career practitioner + toolkit | ★★★ 3 tầng + portal + phụ huynh | → vai trò & tính năng **theo ECG** |
| **Sức khỏe tinh thần** | Trong SEL | ★★★ NL4 riêng (2022) | Trong CCE/Growth Mindset | → module riêng **theo ABCD NL4** |
| **Bản thiết kế portal số** | Không | Poster/guide | ★★★ MySkillsFuture phân tầng | → UX tham chiếu **theo ECG** |
| **Dễ bản địa hóa VN** | Thấp (đặc thù Mỹ) | ★★ Trung bình | ★★ Trung bình (đặc thù SG nhưng Á Đông) | → ECG gần văn hóa nhất |

---

## 3. ⭐ Vấn đề cốt lõi: ba framework dùng **hai trục bị nhầm là một**

Đây là phát hiện quan trọng nhất khi định hợp nhất. Các “giai đoạn” của ba framework **không cùng một trục**:

- **NCDG K → A → R** là **trục ĐỘ SÂU NHẬN THỨC** (Bloom): *bạn biết năng lực này sâu đến đâu* (nhớ → vận dụng → phản tư). **Phi tuổi, áp cho từng năng lực.**
- **ABCD Awareness→…→Advancing** và **ECG Awareness→Exploration→Planning** là **trục GIAI ĐOẠN PHÁT TRIỂN NGHỀ**: *bạn đang ở đâu trong hành trình nghề nghiệp tổng thể*.

Hai trục **trực giao**. Một học sinh lớp 8 đang ở **giai đoạn phát triển = Exploration** (trục dọc), nhưng với riêng năng lực “ra quyết định nghề” em mới ở **độ sâu = K** (mới nhận biết), còn năng lực “khái niệm bản thân” đã đạt **A** (thực hành được). Nếu gộp hai trục làm một, ta mất khả năng vừa định vị hành trình vừa đo thuần thục.

**Thiết kế đề xuất cho WeUp Career — mô hình 2 trục:**

```
                      Trục ĐỘ SÂU (đo thuần thục, theo NCDG / CTGDPT)
                      K (Nhận biết) → A (Thực hiện/Vận dụng) → R (Phản tư)
                      ───────────────────────────────────────────────►
  Trục GIAI ĐOẠN   │
  PHÁT TRIỂN       │   mỗi (năng lực × người học) có MỘT toạ độ (phase, depth)
  (định vị hành    │   tiến bộ = di chuyển sang phải trên trục độ sâu,
   trình, theo ECG)│   và/hoặc thăng giai đoạn trên trục dọc
  Awareness         │
  Exploration       │   Học sinh: phase gắn cấp lớp (ECG) — mặc định, có thể lệch
  Planning          │   Người đi làm: phase phi tuyến (ABCD) — tự do quay vòng
  ▼
```

- **Trục giai đoạn phát triển** = ECG 3 giai đoạn (mặc định gắn `school_level` cho học sinh; cho phép lệch cá nhân). Người đi làm dùng **biến thể phi tuyến ABCD** (có thể đồng thời nhiều giai đoạn ở các domain khác nhau).
- **Trục độ sâu** = K-A-R của NCDG, áp **cho từng năng lực** trong cây ABCD. Dùng làm thước đo tiến bộ và nhãn cho nội dung/câu hỏi.
- **CTGDPT 2018** đã có “Nhận biết → Thực hiện → Vận dụng” ⇒ trục độ sâu **nói được tiếng Việt giáo dục** mà không cần phát minh thang mới.

---

## 4. Mô hình năng lực hợp nhất cho WeUp Career

**Cây năng lực gốc = 12 năng lực ABCD trong 3 lĩnh vực**, được **làm giàu** bằng chỉ báo K-A-R kiểu NCDG và **gắn nhãn pháp lý Điều 5**. Mỗi node năng lực mang đồng thời: (i) mã năng lực ABCD, (ii) các chỉ báo K-A-R đo được (kiểu NCDG), (iii) nhãn Điều 5 TT 16/2026, (iv) instrument tự đánh giá liên quan (VIPS/RIASEC).

| Lĩnh vực (ABCD) | Năng lực | Đo lường (kiểu NCDG) | Nhãn Điều 5 |
|---|---|---|---|
| **A. Quản lý bản thân** | NL1 Khái niệm bản thân tích cực | ≈ SEL1 (K-A-R) + VIPS + RIASEC | **(b)** |
| | NL2 Tương tác với người khác | ≈ SEL2 | (b) |
| | NL3 Thay đổi & phát triển suốt đời | ≈ SEL3 | (b)/(c) |
| | **NL4 Sức khỏe tinh thần & thể chất ★** | (ABCD-riêng; gắn TT 18/2025) | (b) |
| **B. Khám phá học tập & công việc** | NL5 Học tập suốt đời | ≈ ALL1 + ALL2 | (d)/(a) |
| | NL6 Thông tin nghề nghiệp | ≈ CD3 | **(a)** |
| | NL7 Công việc–xã hội–kinh tế | ≈ CD5 | (a) |
| | NL8 Thay đổi vai trò cuộc sống/công việc | ≈ SEL4 (một phần) | (a)/(c) |
| **C. Xây dựng nghề nghiệp** | NL9 Tìm/tạo & duy trì việc làm | ≈ CD4 | (d) |
| | NL10 Ra quyết định nghề | ≈ CD2 | **(c)** |
| | NL11 Cân bằng vai trò cuộc sống/công việc | ≈ SEL4 | (b)/(c) |
| | NL12 Quản lý quá trình xây dựng nghề nghiệp | ≈ CD1 | **(c)** |

> Cây năng lực này là **bộ phân loại pedagogical**. Nó **không thay** bộ phân loại pháp lý Điều 5 — hai bộ chạy song song và **mọi nội dung gắn cả hai nhãn** (xem §5).

---

## 5. ⭐ Crosswalk pháp lý: năng lực quốc tế → **TT 16/2026 Điều 5** (lớp ràng buộc)

Đây là điểm khớp khiến sản phẩm vừa **có nền quốc tế** vừa **tuân thủ pháp luật VN**. 5 nội dung Điều 5 (xem [`legal-basis.md` §4.5](../legal/legal-basis.md)) **không** ánh xạ 1:1 với 12 năng lực — cần bảng quy đổi để gắn **đồng thời 2 nhãn** cho mỗi đơn vị nội dung/câu hỏi (truy vết pháp lý + nền pedagogical):

| Điều 5 (bắt buộc) | Năng lực quốc tế hậu thuẫn | Instrument | Ghi chú ràng buộc |
|---|---|---|---|
| **(a) Thông tin nghề nghiệp** | ABCD NL6, NL7, NL8 · NCDG CD3, CD5 | — | Nguồn nội dung: **Sách tra cứu nghề ILO VN** ([`sources.md`](./sources.md) §2). Minh bạch nguồn. |
| **(b) Nhận thức bản thân** | ABCD NL1, NL2, NL4 · NCDG SEL1, SEL2 | **VIPS + RIASEC** | ⚠️ **Kết quả = dữ liệu nhạy cảm tiềm năng** (legal-basis §6): gắn cờ nhạy cảm, mã hóa, audit log. |
| **(c) Kỹ năng lựa chọn nghề** | ABCD NL10, NL12, NL3 · NCDG CD1, CD2 | mô hình ra quyết định | Đầu ra = **gợi ý có lý do**, người dùng/giám hộ/giáo viên quyết định (human-in-the-loop, Luật AI 134/2025 Đ.4). |
| **(d) Trải nghiệm nghề** | ABCD NL5, NL9 · NCDG CD4, ALL2 | — | Mô phỏng “một ngày làm nghề”; kết nối DN/GDNN (giai đoạn sau). |
| **(đ) CNTT & chuyển đổi số** | (xuyên suốt) + **TT 02/2025** Khung năng lực số | — | Là **chính nền tảng**; đồng thời là một trục năng lực số của người học. |

**Hệ quả data model:** mỗi `content_item` / `assessment_item` cần **hai khóa phân loại**: `dieu5_code ∈ {a,b,c,d,đ}` (pháp lý) **và** `competency_code ∈ {NL1..NL12}` (pedagogical), cộng `depth ∈ {K,A,R}` và `dev_phase ∈ {awareness, exploration, planning}`.

---

## 6. Hệ quả trực tiếp lên Data Model & tính năng (đầu vào cho `spec.md`)

> `docs/spec.md` hiện vẫn là **placeholder Todo app** — cần viết lại theo domain hướng nghiệp. Dưới đây là các thực thể/lĩnh vực mà 3 framework **buộc** phải có:

**Thực thể lõi (gợi ý):**
- `Competency` — cây 12 ABCD × 3 lĩnh vực; `code`, `area`, `name_vi/en`, `dieu5_codes[]`.
- `Indicator` — chỉ báo kiểu NCDG dưới mỗi competency; `competency_id`, `depth ∈ {K,A,R}`, `statement_vi`, `dieu5_code`. **Tuyển chọn**, không bê nguyên NCDG.
- `DevelopmentPhase` — enum `{awareness, exploration, planning}` (ECG); với người đi làm cho phép **nhiều phase đồng thời** (ABCD phi tuyến) → quan hệ N-N qua `LearnerDomainPhase`.
- `AssessmentInstrument` / `AssessmentResult` — RIASEC, VIPS; **`is_sensitive = true`** mặc định (legal-basis §6) → mã hóa + kiểm soát truy cập + audit.
- `LearnerProgress` — toạ độ `(competency, depth)` theo thời gian = đường tiến bộ K→A→R.
- `ContentItem` — gắn `competency_id`, `dieu5_code`, `depth`, `dev_phase`, **`school_level`** (versioned, cập nhật định kỳ — TT 16/2026 yêu cầu).
- `Recommendation` — gợi ý ngành/nghề/lộ trình: **luôn kèm `rationale`** + cờ `requires_human_confirmation` (human-in-the-loop).

**Vai trò (theo mô hình 3 tầng ECG + ràng buộc VN):**
- `student`, `working` (trục `user_type` — đã ghi ở legal-basis §13).
- `guardian` — **bắt buộc cho người dùng <16** (đồng ý của người đại diện theo pháp luật; legal-basis §6). ECG củng cố vai trò này bằng “VIPS conversations với phụ huynh” → tính năng đồng-xem/đồng-ý.
- `counselor`, `school_admin` — kênh B2B2C hợp pháp (TT 18/2025, TT 20/2023).

**Tính năng bắt buộc rút ra từ framework:**
1. **Onboarding theo 3 câu hỏi ECG** (Tôi là ai / muốn đi đâu / đến bằng cách nào) → khung UX tự nhiên.
2. **Bộ test VIPS + RIASEC** (ánh xạ item ILO VN) — *(b)*, gắn cờ nhạy cảm.
3. **Thư viện ngành/nghề** (nguồn ILO) — *(a)*.
4. **Lộ trình ra quyết định** với gợi ý-có-lý-do, không ép buộc — *(c)*.
5. **Module sức khỏe tinh thần (ABCD NL4)** — gắn tư vấn học đường (TT 18/2025).
6. **Bảng tiến bộ K-A-R** per năng lực (đo lường NCDG) — biến hướng nghiệp thành hành trình theo dõi được.
7. **Lớp người đi làm phi tuyến** (ABCD + SkillsFuture): cho phép quay lại Awareness/Exploring khi chuyển nghề; module upskilling.
8. **Hỗ trợ 3 tầng** (đại trà → nhóm → cá nhân) phản ánh trong phân quyền & loại nội dung.

---

## 7. Quyết định áp dụng — **Adopt / Adapt / Reject** (kèm lý do)

| Yếu tố | Quyết định | Lý do |
|---|---|---|
| ECG 3 giai đoạn gắn cấp lớp | **ADOPT** làm trục phát triển chính (học sinh) | Khớp cấu trúc lớp VN + CTGDPT 2018 “yêu cầu cần đạt theo cấp”. |
| ABCD 12 năng lực × 3 lĩnh vực | **ADOPT** làm cây năng lực gốc | Từ vựng dễ đọc cho HS/PH/GV; bao phủ đủ rộng. |
| ABCD phi tuyến (5 giai đoạn) | **ADOPT** làm lớp phủ cho `working` | Chỗ dựa duy nhất cho segment người đi làm/chuyển nghề. |
| ABCD NL4 (sức khỏe tinh thần) | **ADOPT** thành module riêng | Khớp TT 18/2025; khác biệt hóa sản phẩm. |
| NCDG K-A-R + hệ mã hóa | **ADOPT** làm lớp đo lường | Thứ duy nhất cho phép đo tiến bộ; khớp “Nhận biết–Thực hiện–Vận dụng”. |
| VIPS + RIASEC | **ADOPT** làm instrument | Chuẩn quốc tế; ánh xạ item ILO VN sẵn có. |
| ECG portal/3 tầng/phụ huynh | **ADAPT** thành vai trò & tính năng | Lấy *mẫu hình*; vai trò `guardian` là **bắt buộc pháp lý** ở VN, không chỉ “nice-to-have”. |
| SkillsFuture (suốt đời người lớn) | **ADAPT** cho lớp `working`/upskilling | Mẫu hình credit/work-study/coach; bản địa hóa theo Luật GDNN 124/2025. |
| Hàng trăm chỉ báo NCDG nguyên si | **REJECT (bê nguyên)** → tuyển chọn | Phình nội dung + đặc thù Mỹ; chỉ lấy phương pháp + tập con. |
| Định chế Singapore (PSLE/JC/ITE/EAE) | **REJECT** | Đặc thù SG; thay bằng cấu trúc VN (THCS/THPT/GDNN/**trường trung học nghề** — Luật GDNN 124/2025). |
| Tính năng MySkillsFuture cụ thể | **REJECT làm spec** → dùng tham chiếu UX | Tránh sao chép; chỉ học pattern phân tầng theo cấp. |

---

## 8. Cảnh báo bản địa hóa & câu hỏi mở (cần PO xác nhận)

**Cảnh báo (ràng buộc cứng):**
- **Kết quả RIASEC/VIPS = dữ liệu nhạy cảm** theo Luật 91/2025 (legal-basis §6). Ba framework xử lý RIASEC rất thoải mái; luật VN thì **không**. Lớp assessment phải mã hóa + kiểm soát truy cập + audit ngay từ MVP.
- **Không ép buộc phân luồng** (TT 16/2026 + Luật 123/2025) + **AI human-in-the-loop** (Luật 134/2025 Đ.4): giai đoạn “Planning” chỉ tạo **gợi ý kèm lý do**, không tự động quyết định.
- **Giám hộ <16:** mô hình phụ huynh của ECG không chỉ “tốt” mà **bắt buộc pháp lý** ở VN — phải có ngay từ MVP, không bổ sung sau.
- **Bias testing** bộ test/thuật toán theo giới/vùng/hoàn cảnh (Luật 134/2025 Đ.4) — RIASEC không được khóa cứng lựa chọn theo định kiến.

**Câu hỏi mở để PO quyết định:**
1. **MVP nhắm segment nào trước** — học sinh THCS (lớp 8, đúng trọng tâm 3 tài liệu gốc) hay bao gồm luôn `working`? (Ảnh hưởng việc có cần lớp phi tuyến ABCD ngay từ đầu hay không.)
2. **Độ sâu trục đo:** MVP dừng ở **K + A** (phù hợp lứa 13–14, như khuyến nghị NCDG §6.2) hay làm cả **R**?
3. **Phạm vi instrument:** chỉ RIASEC, hay RIASEC + VIPS đầy đủ (+ MBTI như legal-basis có nhắc)?
4. **Có viết lại `docs/spec.md`** theo domain hướng nghiệp ngay sau tài liệu này không? (Hiện vẫn là placeholder Todo.)

---

## 9. Tài liệu liên quan

- 3 framework gốc: `docs/temp/Framework_{NCDG_NCDA,ABCD_CICA,ECG_Singapore}_HuongNghiep.md`
- Ràng buộc pháp lý: [`docs/legal/legal-basis.md`](../legal/legal-basis.md) (§4.5 Điều 5, §6 BVDLCN, §7.1 chuỗi căn cứ AI, §13 data model)
- Thư viện nguồn nền: [`docs/research/sources.md`](./sources.md) (§2 bộ ILO VN — nguồn item trắc nghiệm & thư viện nghề)
- Thực trạng VN: `docs/temp/Thuc_trang_huong_nghiep_Viet_Nam.md`
