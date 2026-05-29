# DPIA — Đánh giá Tác động Bảo vệ Dữ liệu & Rủi ro AI — WeUp Career

**Phiên bản:** 1.0.0 (DRAFT) · **Ngày:** 2026-05-29 · **Trạng thái:** Chờ rà soát pháp chế + cập nhật trước phát hành
**Phạm vi:** Nền tảng Hướng nghiệp Quốc gia WeUp Career ([`docs/spec.md`](../spec.md) v2.0.0)

> Tài liệu này gộp **hai nghĩa vụ đánh giá bắt buộc**:
> 1. **ĐTĐ — Đánh giá tác động xử lý dữ liệu cá nhân** (Luật BVDLCN **91/2025/QH15**, hiệu lực 01/01/2026; NĐ 356/2025). WeUp Career **không được hoãn** ĐTĐ vì xử lý **dữ liệu trẻ em (<16)** và **dữ liệu nhạy cảm tiềm năng** (kết quả trắc nghiệm) — xem [`legal-basis.md` §6 mục 6](legal-basis.md).
> 2. **Đánh giá rủi ro hệ thống AI** (Luật Trí tuệ nhân tạo **134/2025/QH15**, hiệu lực 01/3/2026) — lõi gợi ý ngành/nghề ([`legal-basis.md` §7.1](legal-basis.md)).
>
> Bổ trợ: đánh giá rủi ro dữ liệu định kỳ (Luật Dữ liệu 60/2024 + NĐ 165/2025). Neo evidence: [`docs/validation/weup-career/`](../validation/weup-career/) (threat model, fitness functions, pre-mortem), [`docs/formal-verification/TLC_REPORT.md`](../formal-verification/TLC_REPORT.md) (CP-1…CP-8).
>
> ⚠️ **Đây là bản thảo kỹ thuật** để pháp chế hoàn thiện thành hồ sơ nộp/lưu theo mẫu cơ quan quản lý. **Không thay thế tư vấn pháp lý.**

---

## PHẦN A — ĐÁNH GIÁ TÁC ĐỘNG XỬ LÝ DỮ LIỆU CÁ NHÂN (ĐTĐ)

### A.1. Bên kiểm soát / [CRED_FF7BCA0F] dữ liệu
| Mục | Nội dung |
|---|---|
| Tổ chức | WeUp Career (điền pháp nhân vận hành) |
| Vai trò | Bên Kiểm soát dữ liệu cá nhân (đồng thời Bên Xử lý cho dữ liệu do trường cung cấp — kênh B2B2C) |
| DPO / [CRED_C6B82C5F] | _TBD — chỉ định trước phát hành_ |
| Tư cách với CSDL GD&ĐT | **"Tổ chức khác"** theo NĐ 88/2026 Đ.4 ⇒ xử lý dữ liệu GD trong phạm vi chức năng, **bảo vệ quyền chủ thể theo Luật 91/2025**; **không** áp lưu trữ vĩnh viễn (xem [`legal-basis.md` §9.1](legal-basis.md)) |

### A.2. Mục đích xử lý
Hiện thực hóa **5 nội dung Điều 5 TT 16/2026**: (a) thông tin nghề, (b) trắc nghiệm nhận thức bản thân, (c) kỹ năng chọn nghề, (d) trải nghiệm nghề, (đ) nền tảng số; cộng **gợi ý ngành/nghề/lộ trình** và **theo dõi tiến bộ năng lực**. Cơ sở pháp lý: đồng ý của chủ thể (hoặc người giám hộ với trẻ <16) + thực hiện nhiệm vụ giáo dục theo TT 16/2026.

### A.3. Bản đồ dữ liệu (theo data model `spec.md` §5)

| Thực thể | Loại dữ liệu | Phân loại | Chủ thể |
|---|---|---|---|
| `User` (email, date_of_birth, age_band, user_type, school_level) | Định danh + nhân khẩu | **Cơ bản** | Học sinh, người đi làm; **gồm trẻ <16** |
| `GuardianLink`, `GuardianConsent` | Quan hệ giám hộ, trạng thái đồng ý | Cơ bản | Trẻ <16 + người giám hộ |
| `AssessmentResult` (RIASEC/VIPS/MBTI) | Tính cách/sở thích/giá trị | **★ NHẠY CẢM tiềm năng** (chạm "đời sống riêng tư" — Luật 91/2025) | Người học |
| `LearnerProgress`, `LearnerDomainPhase` | Dữ liệu học tập/tiến bộ | Cơ bản | Người học |
| `Recommendation` (+ rationale) | Suy luận/đầu ra AI về định hướng | **Nhạy cảm tiềm năng** (suy luận hồ sơ) | Người học |
| `CounselingSession` (notes) | Ghi chú tư vấn học đường | **Nhạy cảm** (TT 18/2025 — bảo mật) | Học sinh |
| `AuditLog` | actor id, hành động | Cơ bản (vận hành) | Tất cả |
| `RefreshToken` | Token hash | Cơ bản (auth) | Người dùng |
| `CareerProfile`, `ContentItem` | Thông tin nghề/nội dung | **Không phải DLCN** | — |

### A.4. Bên nhận dữ liệu & chuyển ra nước ngoài
| Bên nhận | Phạm vi | Ghi chú |
|---|---|---|
| Người giám hộ (đã verified) | Dữ liệu trẻ được liên kết | Quyền đồng xem (CP-4) |
| Counselor/school_admin | Học sinh trong `school_id`; dữ liệu đã gỡ nhạy cảm theo quyền | RBAC quan hệ (CP-4, FF-05) |
| CSDL quốc gia GD&ĐT (giai đoạn sau) | Adapter có kiểm soát | NĐ 88/2026 Đ.17 |
| HTTT thị trường lao động (sau) | Chỉ dữ liệu nghề (không DLCN) | — |
| **Nhà cung cấp hosting/AI** | **QUYẾT ĐỊNH MỞ** | ⚠️ Nếu dùng dịch vụ **nước ngoài** ⇒ **đánh giá tác động chuyển dữ liệu xuyên biên giới trong 60 ngày** (Luật 91/2025) + quy tắc Luật Dữ liệu 60/2024. **Khuyến nghị: ưu tiên lưu trữ trong nước.** |

### A.5. Thời hạn xử lý & xóa/hủy
- Dữ liệu lưu **theo mục đích**, không vĩnh viễn (NĐ 88/2026 Đ.4 không áp lưu vĩnh viễn cho "tổ chức khác").
- Xóa tài khoản: soft delete + cửa sổ khôi phục → **purge cứng** (FR-92).
- Thu hồi đồng ý (CP-2): dừng xử lý mới; dữ liệu cũ xử lý theo chính sách lưu trữ/xóa.
- Kết quả trắc nghiệm: versioned; chủ thể/giám hộ **xuất/xóa** được (FR-14, FR-92).

### A.6. Biện pháp bảo vệ (đã thiết kế)
| Biện pháp | Hiện thực | Bằng chứng |
|---|---|---|
| Đồng ý giám hộ <16 (cổng tập trung) | Consent Guard, cấm self-consent | CP-1/CP-2, ADR-010, FF-01/02 |
| Mã hóa dữ liệu nhạy cảm at-rest | Field Crypto (`FIELD_ENCRYPTION_KEY`) | ADR-011, FF-04 |
| Audit mọi truy cập nhạy cảm (fail-closed) | Audit Writer cùng giao dịch | CP-3, FF-03 |
| Kiểm soát truy cập quan hệ | RBAC guardian/counselor theo trường | CP-4, FF-05 |
| Tối thiểu hóa & không lộ kênh phụ | Không log/cache nội dung nhạy cảm | NFR-06/10, FF-10 |
| Quyền chủ thể dữ liệu | Truy cập/xuất/xóa/rút đồng ý | FR-14/92, runbook R6 |
| Bảo mật phiên | JWT ngắn hạn + refresh xoay vòng | CP-7, FF-08 |

### A.7. Đánh giá mức độ rủi ro (likelihood × impact) & tồn dư

| Rủi ro | L | I | Mitigation | Tồn dư |
|---|---|---|---|---|
| Rò rỉ kết quả trắc nghiệm trẻ <16 | Thấp | **Rất cao** | Mã hóa + audit + RBAC + no-log (A.6) | Thấp |
| Xử lý dữ liệu <16 không đồng ý | Thấp | **Rất cao** | Consent Guard (CP-1, TLA+ chứng minh) | Thấp |
| Giả mạo giám hộ | **TB** | Cao | ✅ Luồng VNeID phân tầng (quan hệ do CSDL dân cư khẳng định); dữ liệu nhạy cảm cần ≥MEDIUM — `docs/security/guardian-verification.md` | Thấp sau khi tích hợp VNeID; LOW interim không mở dữ liệu nhạy cảm |
| Truy cập chéo trường/tenant | Thấp | Cao | RBAC quan hệ (CP-4) | Thấp |
| Chuyển dữ liệu xuyên biên giới trái phép | TB | Cao | Ưu tiên hosting trong nước; ĐTĐ 60 ngày nếu ra nước ngoài | **Mở — A.4** |
| Suy luận nhạy cảm từ rationale gợi ý | Thấp | TB | Tối thiểu hóa rationale | Cần kiểm khi build engine |

### A.8. Kết luận Phần A
WeUp Career **thuộc diện phải làm ĐTĐ ngay** (trẻ em + nhạy cảm, không hoãn). Biện pháp kỹ thuật đã thiết kế ở mức cao và phần lớn được **kiểm chứng hình thức (CP-1…CP-7)** + **fitness functions**. **Tồn dư cần đóng trước phát hành:** quyết định hosting/AI (xuyên biên giới — A.4), tăng cường xác thực giám hộ (P-4).

---

## PHẦN B — ĐÁNH GIÁ RỦI RO HỆ THỐNG AI (Luật 134/2025)

### B.1. Mô tả hệ thống AI
Lõi **Recommendation Engine**: gợi ý ngành/nghề/lộ trình & gợi ý phân luồng dựa trên kết quả trắc nghiệm + hồ sơ + tiến bộ năng lực. Người dùng/giám hộ/giáo viên ra quyết định cuối.

### B.2. Phân loại rủi ro (tự phân loại)
**Đề xuất: TRUNG BÌNH → CAO.** Lý do: tác động tới **định hướng giáo dục/tương lai của trẻ vị thành niên**. ⇒ **Tự phân loại + thông báo Bộ KH&CN** qua cổng một cửa AI (Luật 134/2025). _Hành động: nộp thông báo trước phát hành — P-2b._

### B.3. Nghĩa vụ ↔ hiện thực

| Nghĩa vụ Luật 134/2025 | Hiện thực WeUp Career | Trạng thái |
|---|---|---|
| Con người làm trung tâm — AI không thay quyết định (Đ.4) | Human-in-the-loop; không auto-apply | ✅ CP-5, FF-07 |
| Minh bạch / cost giải trình được | `rationale` NOT NULL mọi gợi ý | ✅ CP-6, FF-06 |
| Không thiên lệch / [CRED_82636459] phân biệt | **Bias testing** M1–M5 (counterfactual≥99%, DIR≥0.80) — `docs/testing/bias-testing.md`; job CI wired | ✅ khung + CI wired; execution chờ engine |
| Nhật ký vận hành (hệ thống rủi ro cao) | Lưu input→mô hình/phiên bản→rationale→người duyệt→thời điểm | ✅ thiết kế (AuditLog, legal-basis §13) |
| Con người giám sát/can thiệp được | Xác nhận/từ chối/để sau; counselor tham gia | ✅ CP-5 |
| Hồ sơ kỹ thuật + đánh giá sự phù hợp | Hồ sơ mô hình/phiên bản | ⬜ Lập khi có engine |
| Gắn nhãn nội dung AID (deepfake) | Không sinh nội dung deepfake | N/A |
| Thông báo Bộ KH&CN | Tự phân loại + thông báo | ⬜ **P-2b** |

### B.4. Tồn dư Phần B
- **P-1**: bias-test chưa enforce trong CI — **chặn phát hành** hệ thống rủi ro cao.
- **P-2b**: thông báo phân loại rủi ro tới Bộ KH&CN + hồ sơ kỹ thuật — lập khi engine thành hình.

---

## PHẦN C — RỦI RO DỮ LIỆU ĐỊNH KỲ (Luật Dữ liệu 60/2024 + NĐ 165/2025)
- Phân loại dữ liệu nền tảng; đối chiếu tiêu chí **dữ liệu quan trọng/cốt lõi**.
- Lập quy trình **đánh giá rủi ro dữ liệu định kỳ hằng năm** (gắn vào vận hành — runbook).

---

## PHẦN D — PUNCH LIST (đóng trước phát hành)

| ID | Hạng mục | Phần | Làm được ngay? |
|---|---|---|---|
| **P-1** | Bias-test CI job + tiêu chí công bằng | B.3 | ✅ **khung + CI wired** (`docs/testing/bias-testing.md`); execution chờ engine |
| **P-2b** | Thông báo phân loại rủi ro AI → Bộ KH&CN + hồ sơ kỹ thuật | B.2/B.3 | ⬜ khi có engine |
| **P-4** | Tăng cường xác thực giám hộ (VNeID) | A.7 | ✅ **thiết kế xong** (`docs/security/guardian-verification.md`); execution chờ tích hợp C06 |
| **D-1** | Quyết định hosting/AI; nếu nước ngoài → ĐTĐ chuyển xuyên biên giới (60 ngày) | A.4 | Quyết định kinh doanh |
| **D-2** | Chỉ định DPO/đầu mối; hoàn thiện hồ sơ ĐTĐ theo mẫu cơ quan | A.1 | ✅ |
| **D-3** | Quy trình tiếp nhận yêu cầu chủ thể dữ liệu (đã có tool — runbook R6) | A.5 | ✅ |
| **D-4** | Rà soát pháp chế toàn bộ DPIA | tất cả | ⬜ |

> **Verdict:** DPIA bản thảo hoàn tất, neo đầy đủ vào thiết kế + bằng chứng hình thức. **Chưa đủ điều kiện phát hành** đến khi đóng P-1, P-2b, P-4, D-1, D-4. Cập nhật DPIA mỗi khi: đổi nhà cung cấp hosting/AI, mở rộng loại dữ liệu, hoặc thay đổi lõi thuật toán gợi ý.
