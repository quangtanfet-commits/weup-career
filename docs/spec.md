# NLSpec: Nền tảng Hướng nghiệp Quốc gia — WeUp Career

**Phiên bản:** 2.0.0
**Ngày:** 2026-05-29
**Trạng thái:** DRAFT — Chờ phê duyệt triển khai
**Tác giả:** Engineering Team
**Thay thế:** v1.0.0 (spec Todo app — placeholder, đã loại bỏ)

> **Quy ước ngôn ngữ:** Văn xuôi/đặc tả bằng tiếng Việt (đồng bộ với `docs/legal/legal-basis.md`, `docs/research/`). Định danh kỹ thuật (entity, field, enum, API path, mã FR/NFR) giữ tiếng Anh.
>
> **Căn cứ nền:**
> - Pháp lý ràng buộc: [`docs/legal/legal-basis.md`](./legal/legal-basis.md) — đặc biệt **§4.5 (TT 16/2026 Điều 5)**, **§6 (BVDLCN)**, **§7.1 (chuỗi căn cứ AI)**, **§13 (hệ quả data model)**.
> - Lý luận–thiết kế: [`docs/research/career-frameworks-synthesis.md`](./research/career-frameworks-synthesis.md) — mô hình 2 trục, cây 12 năng lực, crosswalk Điều 5.
> - Nguồn nội dung: [`docs/research/sources.md`](./research/sources.md) — bộ ILO Việt Nam (thư viện nghề & item trắc nghiệm).

---

## 1. MỤC ĐÍCH (PURPOSE)

Xây dựng **WeUp Career** — nền tảng số hướng nghiệp quốc gia cho học sinh, sinh viên và người đi làm tại Việt Nam. Hệ thống cung cấp 5 nội dung hướng nghiệp bắt buộc theo **TT 16/2026/TT-BGDĐT Điều 5**, dựa trên **bộ công cụ tự đánh giá chuẩn quốc tế** (RIASEC, VIPS, MBTI), một **mô hình năng lực hợp nhất** (12 năng lực ABCD × 3 lĩnh vực, đo theo trục K-A-R kiểu NCDG), và **gợi ý ngành/nghề/lộ trình có giải thích** theo nguyên tắc **con người ra quyết định cuối cùng** (human-in-the-loop).

Nền tảng số này **chính là** nội dung "(đ) Ứng dụng CNTT & chuyển đổi số trong hướng nghiệp" — vừa là sản phẩm, vừa được pháp luật hợp pháp hóa & yêu cầu (Luật 123/2025 Đ.19, CT 29-CT/TW, TT 16/2026 Đ.5đ).

### Mục tiêu (Goals)
- **G-01:** Hiện thực hóa **đủ 5 nội dung Điều 5** thành module có căn cứ pháp lý minh bạch, mỗi đơn vị nội dung gắn `dieu5_code` + `competency_code`.
- **G-02:** Đo được **tiến bộ năng lực hướng nghiệp** của người học theo mô hình **2 trục**: *giai đoạn phát triển* (Awareness → Exploration → Planning) × *độ sâu nhận thức* (K → A → R).
- **G-03:** Cung cấp **trắc nghiệm định hướng** (RIASEC + VIPS + MBTI) với xử lý **dữ liệu nhạy cảm** đúng Luật 91/2025 ngay từ MVP.
- **G-04:** **Gợi ý ngành/nghề/lộ trình bằng thuật toán/AI có kiểm soát** — luôn kèm lý do, không ép buộc, người dùng/giám hộ/giáo viên quyết định.
- **G-05:** Hỗ trợ **luồng đăng ký & đồng ý của người giám hộ cho người dùng <16 tuổi** ngay từ MVP (không bổ sung sau).
- **G-06:** Mô hình hóa **kênh trường học B2B2C** (giáo viên/tư vấn học đường, quản trị trường) theo mô hình hỗ trợ 3 tầng.
- **G-07:** Kiến trúc **mở rộng được** sang Tiểu học và người đi làm mà không phải viết lại lõi (cây năng lực & 2 trục là bất biến; phân tầng theo `school_level`/`user_type`).

### Phạm vi MVP & lộ trình mở rộng
- **MVP (giai đoạn 1):** Học sinh **THCS + THPT** (lớp 6–12). Trọng tâm giai đoạn **Exploration** (THCS) và **Planning** (THPT). Đầy đủ trục đo **K + A + R**.
- **Giai đoạn 2:** Mở rộng **Tiểu học** (trọng tâm Awareness) — nội dung & UX đơn giản hóa theo lứa tuổi.
- **Giai đoạn 3:** **Người đi làm** (`user_type = working`) — kích hoạt **lớp phát triển phi tuyến (ABCD)**, module upskilling/chuyển nghề (tham chiếu mô hình SkillsFuture).

### Phi mục tiêu (Non-Goals)
- **NG-01:** **Không** tự động hóa quyết định phân luồng/chọn nghề — hệ thống chỉ **gợi ý** (ràng buộc Luật 134/2025 Đ.4 + nguyên tắc không ép buộc TT 16/2026).
- **NG-02:** **Không** là nền tảng tuyển sinh/tuyển dụng; tích hợp dữ liệu thị trường lao động & cơ sở đào tạo qua **adapter** (giai đoạn sau), không sở hữu dữ liệu đó.
- **NG-03:** **Không** thay thế tư vấn học đường — bổ trợ và kết nối tới counselor (Tier 3).
- **NG-04:** **Không** dùng MBTI/RIASEC để **khóa cứng** lựa chọn nghề theo định kiến (ràng buộc bias testing).
- **NG-05:** App mobile native — chưa làm ở MVP; web responsive trước.

---

## 2. TÁC NHÂN (ACTORS)

| Tác nhân | Mô tả | Ràng buộc tuổi/pháp lý |
|---|---|---|
| **Anonymous** | Xem trang giới thiệu, đăng ký/đăng nhập; không truy cập dữ liệu hướng nghiệp | — |
| **Student (≥16)** | Học sinh tự đăng ký, tự đồng ý xử lý dữ liệu | `user_type=student`, `age_band≥16` |
| **Student (<16)** | Học sinh; đăng ký & xử lý dữ liệu **phải có đồng ý của người giám hộ** | `age_band<16` → bắt buộc `GuardianConsent` active |
| **Guardian** | Người đại diện theo pháp luật (cha/mẹ/giám hộ); đồng ý, đồng xem hồ sơ/kết quả của trẻ <16 | Liên kết qua `GuardianLink` |
| **Working user** | Người đi làm/chuyển nghề (giai đoạn 3) | `user_type=working` |
| **Counselor** | Nhân viên tư vấn học đường/giáo viên kiêm nhiệm (TT 18/2025) | Vai trò trong phạm vi trường |
| **School admin** | Quản trị cấp trường: quản lý lớp, học sinh, counselor | Phân quyền theo `school_id` |
| **Content editor** | Biên tập nội dung nghề/bài học/item trắc nghiệm (versioned) | Nội bộ |
| **System (Backend)** | Xác thực, phân quyền, lưu trữ, audit, thực thi quy tắc consent & nhạy cảm | — |
| **AI Recommendation Engine** | Sinh gợi ý ngành/nghề/lộ trình **có giải thích**; không tự quyết | Human-in-the-loop, bias-tested, explainable |
| **CI Pipeline** | Chạy quality gate: test, coverage, security, bias test, TLC | — |
| **Operator** | Triển khai, giám sát, xoay khóa, sao lưu, xử lý yêu cầu chủ thể dữ liệu | — |

**Hệ thống ngoài (qua adapter, giai đoạn sau):** CSDL quốc gia về GD&ĐT (NĐ 88/2026), Hệ thống thông tin thị trường lao động, VNeID (xác thực tuổi/giám hộ — NĐ 69/2024).

---

## 3. YÊU CẦU CHỨC NĂNG (FUNCTIONAL REQUIREMENTS)

### 3.1 Định danh, độ tuổi & đồng ý giám hộ (lõi pháp lý)
- **FR-01:** Đăng ký bằng email + mật khẩu; thu thập `date_of_birth` (suy ra `age_band`) và `user_type`.
- **FR-02:** Nếu `age_band < 16`: tài khoản ở trạng thái `pending_guardian_consent`, **không xử lý dữ liệu hướng nghiệp** (trắc nghiệm, gợi ý) cho đến khi có `GuardianConsent` active.
- **FR-03:** Luồng mời/xác nhận giám hộ: trẻ nhập thông tin người giám hộ → guardian xác nhận qua kênh độc lập (email/VNeID) → tạo `GuardianConsent`.
- **FR-04:** Guardian có thể **thu hồi đồng ý** bất kỳ lúc nào → tài khoản trẻ trở lại `pending_guardian_consent`, dừng xử lý dữ liệu mới (dữ liệu cũ xử lý theo chính sách lưu trữ/xóa).
- **FR-05:** Đăng nhập cấp access token ngắn hạn (15 phút) + refresh token httpOnly (7 ngày), refresh xoay vòng, logout thu hồi server-side.
- **FR-06:** Mật khẩu ≥8 ký tự, hoa/thường/số; email chuẩn hóa lowercase/trim; bcrypt cost ≥12.
- **FR-07:** Hỗ trợ liên kết **VNeID** (tùy chọn) để tăng độ tin cậy xác thực tuổi & quan hệ giám hộ (giai đoạn sau).

### 3.2 Trắc nghiệm định hướng — Điều 5(b), dữ liệu nhạy cảm
- **FR-10:** Cung cấp 3 bộ instrument: **RIASEC** (Holland), **VIPS** (Values–Interests–Personality–Skills), **MBTI**. Mỗi bộ là một `AssessmentInstrument` versioned.
- **FR-11:** Người học làm bài → tạo `AssessmentResult` với `is_sensitive=true` mặc định (mã hóa at-rest, kiểm soát truy cập chặt, audit mọi lần đọc).
- **FR-12:** Kết quả trình bày kèm **giải thích** và liên hệ nhóm nghề; **không** kết luận cứng "bạn phải làm nghề X".
- **FR-13:** Item trắc nghiệm gắn `competency_code` (chủ yếu NL1) + `dieu5_code=b`; nguồn ưu tiên bộ **ILO Việt Nam** (sources.md §2).
- **FR-14:** Người học (hoặc guardian với trẻ <16) có thể **xuất/xóa** kết quả trắc nghiệm (quyền chủ thể dữ liệu, Luật 91/2025).
- **FR-15:** Kết quả nhiều lần làm được **versioned** (không ghi đè) để theo dõi thay đổi theo thời gian.

### 3.3 Mô hình năng lực & đo tiến bộ (2 trục K-A-R × dev_phase)
- **FR-20:** Hệ thống lưu **cây năng lực** cố định: 12 `Competency` thuộc 3 lĩnh vực (A/B/C theo ABCD), mỗi competency gắn `dieu5_codes[]`.
- **FR-21:** Mỗi competency có tập `Indicator` (kiểu NCDG) ở 3 độ sâu `depth ∈ {K, A, R}`, phát biểu bằng tiếng Việt (ánh xạ "Nhận biết → Thực hiện → Vận dụng" của CTGDPT 2018).
- **FR-22:** Mỗi người học có `LearnerProgress` ghi toạ độ `(competency, depth)` đạt được theo thời gian, cập nhật khi hoàn thành hoạt động/đánh giá có nhãn tương ứng.
- **FR-23:** Mỗi người học có `dev_phase` hiện tại: với `student` mặc định suy ra từ `school_level` (THCS→Exploration, THPT→Planning) **nhưng cho phép lệch cá nhân**; với `working` cho phép **nhiều dev_phase đồng thời theo domain** (lớp phi tuyến ABCD).
- **FR-24:** Bảng/biểu đồ tiến bộ hiển thị cho người học, guardian (trẻ <16), và counselor (trong phạm vi trường).

### 3.4 Thông tin nghề nghiệp — Điều 5(a)
- **FR-30:** Thư viện ngành/nghề (`CareerProfile`): mô tả, yêu cầu năng lực & phẩm chất, điều kiện đào tạo, cơ hội việc làm, xu hướng thị trường; gắn `dieu5_code=a`, nguồn minh bạch.
- **FR-31:** Thông tin trường/ngành đào tạo, bao gồm nhánh **GDNN & "trường trung học nghề"** (Luật GDNN 124/2025) như một hướng phân luồng sau THCS.
- **FR-32:** Tìm kiếm/lọc nghề theo nhóm RIASEC, lĩnh vực, trình độ đào tạo; liên kết kết quả trắc nghiệm → nghề gợi ý liên quan.
- **FR-33:** Nội dung nghề **versioned** + rà soát/cập nhật định kỳ (yêu cầu TT 16/2026).

### 3.5 Kỹ năng lựa chọn nghề — Điều 5(c)
- **FR-40:** Lộ trình/bài học về quy trình ra quyết định nghề (gắn NL10, NL12; `dieu5_code=c`).
- **FR-41:** Công cụ so sánh ngành/nghề theo tiêu chí cá nhân (giá trị, sở thích, năng lực, điều kiện).
- **FR-42:** Bài tập tình huống/SWOT cá nhân; ghi nhận tiến bộ ở trục K-A-R.

### 3.6 Trải nghiệm nghề — Điều 5(d)
- **FR-50:** Nội dung mô phỏng/"một ngày làm nghề"; gắn NL5, NL9; `dieu5_code=d`.
- **FR-51:** (Giai đoạn sau) Kết nối doanh nghiệp/cơ sở GDNN cho trải nghiệm thực tế.

### 3.7 Gợi ý & phân luồng — Điều 5(đ) + nguyên tắc không ép buộc
- **FR-60:** `AI Recommendation Engine` sinh gợi ý ngành/nghề/lộ trình dựa trên hồ sơ + kết quả trắc nghiệm + tiến bộ năng lực.
- **FR-61:** **Mọi `Recommendation` bắt buộc có `rationale`** (giải thích được) và cờ `requires_human_confirmation=true` — hệ thống không tự thực hiện hành động phân luồng.
- **FR-62:** Gợi ý phân luồng (học tiếp / trung học nghề / GDNN / lao động) chỉ hiển thị như **lựa chọn có lý do**, kèm cảnh báo "quyết định thuộc về bạn/giám hộ/giáo viên".
- **FR-63:** Lưu vết: input → gợi ý → ai xác nhận/bác bỏ (phục vụ giải trình & bias audit).

### 3.8 Module Sức khỏe tinh thần — ABCD NL4 (gắn TT 18/2025)
- **FR-70:** Nội dung quản lý stress, cân bằng, nhận biết khi cần hỗ trợ; gắn NL4, `dieu5_code=b`.
- **FR-71:** Đường dẫn an toàn tới counselor (Tier 3) khi người học có dấu hiệu cần hỗ trợ; **không** chẩn đoán y tế.

### 3.9 Kênh trường học & hỗ trợ 3 tầng (B2B2C)
- **FR-80:** `school_admin` quản lý lớp/học sinh/counselor trong phạm vi `school_id`.
- **FR-81:** Mô hình hỗ trợ 3 tầng: **Tier 1** nội dung đại trà cho mọi học sinh; **Tier 2** hoạt động nhóm mục tiêu; **Tier 3** tư vấn cá nhân (`CounselingSession`).
- **FR-82:** Counselor xem tiến bộ & kết quả (đã gỡ nhạy cảm theo phân quyền) của học sinh được phân công; ghi nhận phiên tư vấn.
- **FR-83:** Phân quyền dữ liệu học sinh tuân thủ nguyên tắc bảo mật/tự nguyện (TT 18/2025) + BVDLCN.

### 3.10 Quản trị nội dung & tài khoản
- **FR-90:** `content_editor` tạo/sửa nội dung với bắt buộc gắn `competency_code`, `dieu5_code`, `depth`, `dev_phase`, `school_level`; versioned.
- **FR-91:** Người dùng xem/sửa hồ sơ; đổi mật khẩu (cần mật khẩu hiện tại); yêu cầu xóa tài khoản (soft delete + cửa sổ khôi phục).
- **FR-92:** Hỗ trợ quyền chủ thể dữ liệu: truy cập, chỉnh sửa, xuất, xóa dữ liệu cá nhân (Luật 91/2025).

---

## 4. YÊU CẦU PHI CHỨC NĂNG (NON-FUNCTIONAL REQUIREMENTS)

| ID | Nhóm | Yêu cầu |
|----|------|---------|
| NFR-01 | Performance | p99 < 150ms cho read; < 300ms cho write ở 200 người dùng đồng thời |
| NFR-02 | Scalability | Kiến trúc tách stateless API; sẵn sàng scale ngang khi thay SQLite → Postgres |
| NFR-03 | Availability | Mục tiêu 99.9% uptime production |
| **NFR-10** | **BVDLCN — dữ liệu nhạy cảm** | Kết quả RIASEC/VIPS/MBTI mã hóa at-rest; kiểm soát truy cập theo vai trò; **audit mọi truy cập** (Luật 91/2025, legal-basis §6) |
| **NFR-11** | **Đồng ý giám hộ** | Không xử lý dữ liệu hướng nghiệp của `age_band<16` khi chưa có `GuardianConsent` active — **bất biến hệ thống**, kiểm chứng bằng TLA+ |
| **NFR-12** | **AI governance** | Mọi gợi ý **giải thích được**; **bias testing** theo giới/vùng/hoàn cảnh định kỳ, tài liệu hóa; **human-in-the-loop** bắt buộc (Luật 134/2025 Đ.4) |
| **NFR-13** | **Phân loại rủi ro AI** | Coi hệ thống gợi ý ở mức rủi ro **TRUNG BÌNH→CAO**; có hồ sơ đánh giá rủi ro/ DPIA trước phát hành (legal-basis §7) |
| NFR-14 | Security | Mọi endpoint xác thực; không vượt quyền; bcrypt cost ≥12; không log PII/token |
| NFR-15 | Security | Rate limit: 20 auth req/phút/IP, 200 API req/phút/user |
| NFR-16 | Audit | Audit log bất biến cho: truy cập dữ liệu nhạy cảm, thay đổi consent, gợi ý AI & xác nhận |
| NFR-17 | Observability | Structured JSON log + correlation ID; health + readiness endpoint |
| NFR-18 | Reliability | Graceful shutdown; request đang xử lý hoàn tất trước khi thoát |
| NFR-19 | Testability | ≥95% line coverage; **100% trên auth, consent, sensitive-data & recommendation layer** |
| NFR-20 | Maintainability | Hợp đồng API tài liệu hóa bằng OpenAPI 3.1 |
| NFR-21 | Accessibility | Frontend đạt WCAG 2.1 AA |
| NFR-22 | Responsiveness | Hoạt động đúng trên viewport 320px–2560px |
| NFR-23 | i18n | Nội dung versioned theo `school_level`; sẵn sàng đa ngôn ngữ (vi mặc định) |
| NFR-24 | Portability | Chạy full stack qua `docker compose up`, không cần thiết lập trước |
| NFR-25 | Data residency | Dữ liệu cá nhân lưu trữ tuân thủ pháp luật VN; để ngỏ adapter CSDL quốc gia GD&ĐT |
| NFR-26 | Content governance | Nội dung nghề rà soát/cập nhật định kỳ (TT 16/2026); có quy trình version & duyệt |

---

## 5. MÔ HÌNH DỮ LIỆU (DATA MODEL)

### Định danh & giám hộ
**User** — `id (UUID, PK)`, `email (unique)`, `hashed_password`, `date_of_birth`, `age_band (enum: under_16, 16_17, adult)`, `user_type (enum: student, working)`, `school_level (enum: primary, lower_secondary, upper_secondary, tertiary, none)`, `account_status (enum: active, pending_guardian_consent, suspended, deleted)`, `is_deleted`, `deleted_at`, `created_at`, `updated_at`.

**GuardianLink** — `id (PK)`, `child_user_id (FK→User)`, `guardian_user_id (FK→User)`, `relationship`, `verified_at`, `verification_method (enum: email, vneid)`.

**GuardianConsent** — `id (PK)`, `child_user_id (FK)`, `guardian_link_id (FK)`, `scope`, `status (enum: active, revoked)`, `granted_at`, `revoked_at`. *(Bất biến NFR-11 dựa trên thực thể này.)*

**RefreshToken** — `id (PK)`, `user_id (FK)`, `token_hash (SHA-256)`, `expires_at`, `revoked_at`, `created_at`, `user_agent`, `ip_address`.

### Mô hình năng lực (2 trục)
**Competency** — `id (PK)`, `code (NL1..NL12)`, `area (enum: A_personal, B_exploration, C_building)`, `name_vi`, `name_en`, `dieu5_codes (array)`.

**Indicator** — `id (PK)`, `competency_id (FK)`, `depth (enum: K, A, R)`, `statement_vi`, `dieu5_code`, `source_ref` *(vd item ILO)*.

**LearnerProgress** — `id (PK)`, `user_id (FK)`, `competency_id (FK)`, `depth_achieved (enum: K, A, R)`, `evidence_ref`, `achieved_at`. *(Lịch sử — không ghi đè.)*

**LearnerDomainPhase** — `id (PK)`, `user_id (FK)`, `domain (enum/area)`, `dev_phase (enum: awareness, exploration, planning)`, `set_at`. *(Cho phép nhiều bản ghi với `working` — phi tuyến.)*

### Trắc nghiệm (dữ liệu nhạy cảm)
**AssessmentInstrument** — `id (PK)`, `type (enum: riasec, vips, mbti)`, `version`, `is_active`.
**AssessmentItem** — `id (PK)`, `instrument_id (FK)`, `competency_code`, `dieu5_code`, `prompt_vi`.
**AssessmentResult** — `id (PK)`, `user_id (FK)`, `instrument_id (FK)`, `result_payload (encrypted)`, `is_sensitive (default true)`, `version`, `created_at`. *(Mọi truy cập → AuditLog.)*

### Nội dung & gợi ý
**CareerProfile** — `id (PK)`, `name`, `riasec_codes`, `required_competencies`, `training_paths`, `labor_market_outlook`, `source_ref`, `version`, `dieu5_code='a'`.
**ContentItem** — `id (PK)`, `title`, `body`, `competency_id (FK)`, `dieu5_code`, `depth`, `dev_phase`, `school_level`, `version`, `status (enum: draft, published, archived)`.
**Recommendation** — `id (PK)`, `user_id (FK)`, `payload`, `rationale (NOT NULL)`, `requires_human_confirmation (default true)`, `confirmed_by (FK→User, nullable)`, `confirmed_decision (enum: accepted, rejected, deferred)`, `created_at`. *(rationale bắt buộc — bất biến CP-6.)*
**Pathway** — `id (PK)`, `name`, `type (enum: academic, vocational_secondary, gdnn, labor)`, `description`.

### Trường học & tư vấn
**School** — `id`, `name`, `type`, `region`.
**SchoolClass** — `id`, `school_id (FK)`, `name`, `grade`.
**CounselingSession** — `id`, `counselor_id (FK→User)`, `student_id (FK→User)`, `tier (enum: 1,2,3)`, `notes`, `created_at`.

### Giám sát
**AuditLog** — `id (PK)`, `actor_id`, `action`, `target_type`, `target_id`, `is_sensitive_access (bool)`, `correlation_id`, `created_at`. *(Append-only.)*

---

## 6. RANH GIỚI API (API BOUNDARIES)

Base: `/api/v1/...`

| Method | Path | Mô tả | Auth |
|--------|------|-------|------|
| POST | /auth/register | Đăng ký (suy ra age_band → consent gate) | No |
| POST | /auth/login | Cấp token | No |
| POST | /auth/refresh | Xoay access token | Cookie |
| POST | /auth/logout | Thu hồi refresh token | Bearer |
| GET | /auth/me | Hồ sơ hiện tại | Bearer |
| POST | /guardians/invite | Trẻ <16 mời giám hộ | Bearer |
| POST | /guardians/consent | Guardian cấp đồng ý | Bearer |
| POST | /guardians/consent/revoke | Guardian thu hồi | Bearer |
| GET | /competencies | Cây 12 năng lực + indicator | Bearer |
| GET | /me/progress | Tiến bộ K-A-R per năng lực | Bearer |
| GET | /assessments | Danh sách instrument (RIASEC/VIPS/MBTI) | Bearer |
| POST | /assessments/{type}/submit | Nộp bài → kết quả (nhạy cảm) | Bearer + consent |
| GET | /me/assessments/{id} | Xem kết quả (audit-logged) | Bearer + consent |
| DELETE | /me/assessments/{id} | Xóa kết quả (quyền chủ thể) | Bearer |
| GET | /careers | Thư viện nghề (lọc RIASEC/lĩnh vực) | Bearer |
| GET | /careers/{id} | Chi tiết nghề | Bearer |
| GET | /content | Nội dung lọc theo dieu5/competency/phase/level | Bearer |
| POST | /recommendations | Sinh gợi ý (kèm rationale) | Bearer + consent |
| POST | /recommendations/{id}/confirm | Người dùng/giám hộ/GV xác nhận | Bearer |
| GET | /school/{id}/students | DS học sinh (phạm vi trường) | Bearer (admin/counselor) |
| POST | /counseling/sessions | Ghi phiên tư vấn | Bearer (counselor) |
| GET | /health | Liveness | No |
| GET | /ready | Readiness | No |

---

## 7. CỔNG CHẤT LƯỢNG (QUALITY GATES)

### Gate A — Hoàn thiện spec (trước triển khai)
- [ ] spec-preflight ≥ 0.85 trên 4 chiều rõ ràng
- [ ] ADR cho: mô hình 2 trục, xử lý dữ liệu nhạy cảm, kiến trúc consent, AI governance
- [ ] Threat model + **DPIA** (đánh giá tác động bảo vệ dữ liệu) hoàn tất
- [ ] TLA+ spec thiết kế cho consent/sensitive-access/recommendation
- [ ] Scenarios viết dưới `scenarios/` (không cho coder xem)

### Gate B — Trước merge (mỗi PR)
- [ ] Test pass (unit + integration + E2E)
- [ ] Coverage ≥95%; 100% trên auth + consent + sensitive-data + recommendation
- [ ] mypy/pyright strict; ESLint + TS strict — zero error
- [ ] Trivy: zero HIGH/CRITICAL; Semgrep: zero security finding; OWASP ZAP baseline: zero HIGH
- [ ] **Bias test bộ trắc nghiệm/thuật toán** pass ngưỡng công bằng đã định
- [ ] TLC model checker pass (nếu đổi state machine consent/recommendation)
- [ ] OpenAPI schema không đổi ngoài ý muốn

### Gate C — Phát hành production
- [ ] Smoke test trên staging
- [ ] Load test: p99 < 150ms ở tải mục tiêu
- [ ] Báo cáo pentest đã rà
- [ ] **Hồ sơ phân loại & đánh giá rủi ro AI** đã duyệt (Luật 134/2025)
- [ ] Quy trình rollback đã kiểm thử

---

## 8. THUỘC TÍNH ĐÚNG ĐẮN (CORRECTNESS PROPERTIES — TLA+)

Các bất biến phải đúng dưới mọi interleaving (xem `docs/formal-verification/`):

1. **Consent invariant (CP-1):** Không tồn tại trạng thái nào hệ thống xử lý/sinh dữ liệu hướng nghiệp (assessment result, recommendation) cho `User` có `age_band=under_16` mà **không** có `GuardianConsent` ở trạng thái `active`.
2. **Consent revocation (CP-2):** Sau khi guardian thu hồi đồng ý, không có thao tác xử lý dữ liệu mới nào của trẻ được chấp nhận cho tới khi consent active trở lại.
3. **Sensitive-access invariant (CP-3):** Mọi lần đọc `AssessmentResult` (`is_sensitive=true`) đều sinh đúng một bản ghi `AuditLog` với `is_sensitive_access=true`; không có đường đọc nào bỏ qua audit.
4. **Ownership invariant (CP-4):** Người dùng không bao giờ đọc/sửa/xóa dữ liệu của người khác, trừ quan hệ được cấp quyền tường minh (guardian↔child, counselor↔student trong phạm vi trường).
5. **Human-in-the-loop (CP-5):** Không có hành động phân luồng/chọn nghề nào được hệ thống tự thực hiện; mọi `Recommendation` chỉ chuyển sang trạng thái có hiệu lực sau khi `confirmed_by` (người) ghi `confirmed_decision`.
6. **Recommendation rationale (CP-6):** Không tồn tại `Recommendation` nào được tạo mà `rationale` rỗng/null.
7. **Token validity (CP-7):** Refresh token đã thu hồi không thể dùng để lấy access token mới.
8. **Progress monotonicity (CP-8):** `depth_achieved` của một (user, competency) chỉ tiến K→A→R, không lùi trong cùng chu kỳ đánh giá hợp lệ (lịch sử được giữ, không ghi đè).

Xem `docs/formal-verification/tla-spec-design.md` cho thiết kế module TLA+ đầy đủ.
