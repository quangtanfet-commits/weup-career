# Threat Model — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Framework:** STRIDE + DREAD
**Phạm vi:** Nền tảng Hướng nghiệp Quốc gia (Backend API + Frontend SPA + Recommendation Engine + Docker)
**Thay thế:** v1.0.0 (threat model Todo app)

> Neo vào [`docs/legal/legal-basis.md`](../legal/legal-basis.md) §6 (BVDLCN), §7 (AI governance) và [`docs/spec.md`](../spec.md) §8 (CP). Tài sản nhạy cảm trọng tâm: **kết quả trắc nghiệm (RIASEC/VIPS/MBTI)**, **dữ liệu trẻ <16**, **gợi ý nghề**.

---

## Tổng quan hệ thống cho threat modeling

```
[Internet]
    │
    ▼
[Nginx — TLS, rate limit, security headers]
    │
    ├──→ [Static — Frontend SPA]
    └──→ [Backend API — FastAPI]
              │  (Auth → Consent Guard → RBAC → Audit)
              ├──→ [Recommendation Engine] (AI có kiểm soát)
              ├──→ [Database] (trường nhạy cảm mã hóa)
              └──→ [Audit Store] (append-only)
```

**Trust boundaries:**
1. Internet → Nginx (TLS; input không tin cậy)
2. Nginx → Backend (mạng Docker nội bộ; tin cậy)
3. Backend → DB / Audit Store (volume; tin cậy)
4. **Backend ↔ Recommendation Engine** (ranh giới AI governance — đầu ra phải có rationale, bias-tested)
5. **Cổng đồng ý giám hộ** (ranh giới pháp lý: dữ liệu trẻ <16)

---

## Phân tích STRIDE

### S — Spoofing

| Mối đe dọa | Tài sản | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| Giả mạo phiên người dùng hợp pháp | Auth tokens | TB | Critical | JWT signature; refresh httpOnly; rotation |
| **Giả mạo người giám hộ để cấp đồng ý cho trẻ <16** | GuardianConsent | TB | **Critical (pháp lý)** | Xác thực giám hộ qua kênh độc lập (email/**VNeID**); GuardianLink.verified_at; không cho self-consent |
| Giả mạo vai trò counselor/school_admin | Phân quyền trường | Thấp | Cao | Cấp tài khoản qua school_admin; ràng buộc school_id |
| Replay refresh token | Refresh token | Thấp | Cao | Single-use rotation; revoke on logout; lưu SHA-256 |
| JWT giả | Access token | Thấp | Critical | HS256 verify; exp enforced |

### T — Tampering

| Mối đe dọa | Tài sản | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| Sửa dữ liệu hướng nghiệp của người khác | Result/Progress | TB | Cao | Ownership check mọi query (CP-4) |
| **Sửa/giả kết quả trắc nghiệm** | AssessmentResult | Thấp | Cao | Mã hóa + versioned (không ghi đè); audit |
| **Sửa `rationale`/bỏ qua human-confirm để ép gợi ý có hiệu lực** | Recommendation | Thấp | **Cao (pháp lý)** | CP-5/CP-6 (TLA+); rationole NOT NULL; chỉ người chuyển trạng thái |
| SQL injection | DB | Thấp | Critical | SQLAlchemy parameterized; Pydantic |
| Sửa response trên đường truyền | Response | Thấp | Cao | HTTPS/HSTS |

### R — Repudiation

| Mối đe dọa | Tài sản | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| Chối truy cập dữ liệu nhạy cảm | Audit trail | TB | **Cao** | **Audit mọi đọc kết quả nhạy cảm (CP-3)**; append-only |
| Chối thay đổi consent | Consent log | Thấp | Cao | Ghi audit granted/revoked + actor |
| Chối ai xác nhận gợi ý | Reco log | Thấp | TB | Lưu confirmed_by + decision (giải trình AI) |
| Sửa log che dấu vết | Log integrity | Rất thấp | TB | Log stdout → shipper; audit store append-only |

### I — Information Disclosure ★ (rủi ro lõi của domain này)

| Mối đe dọa | Tài sản | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| **Lộ kết quả RIASEC/VIPS/MBTI** (dữ liệu nhạy cảm) | AssessmentResult | TB | **Critical** | Mã hóa at-rest (Field Crypto); RBAC chặt; audit; KHÔNG log nội dung; không cache lâu ở client |
| **Lộ dữ liệu trẻ <16** | Hồ sơ trẻ | TB | **Critical (pháp lý)** | Consent gate; quyền xem giới hạn guardian/counselor; tối thiểu hóa dữ liệu |
| Stack trace trong 500 | Kiến trúc nội bộ | Thấp | Thấp | Không lộ trace; generic error |
| Token bị log | Auth tokens | Thấp | Critical | Không log token; strip Authorization |
| Email enumeration | DS email | TB | Thấp | Thông báo generic |
| File DB lộ trên đĩa | Toàn bộ dữ liệu | Rất thấp | Critical | Volume owned appuser; secrets; trường nhạy cảm vẫn mã hóa |
| **Suy luận thông tin nhạy cảm từ gợi ý** | Hồ sơ tâm lý | Thấp | TB | Giải thích gợi ý không lộ chi tiết thô; tối thiểu hóa |

### D — Denial of Service

| Mối đe dọa | Tài sản | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| Brute force login | Tài khoản | Cao | Cao | Rate limit 20/min/IP; bcrypt chậm |
| Flood endpoint trắc nghiệm/gợi ý (tốn tính toán) | Khả dụng | TB | TB | Rate limit per-user; hàng đợi/giới hạn reco |
| Payload lớn | Bộ nhớ | Thấp | Thấp | `client_max_body_size`; Pydantic max length |
| JSON dị dạng | Ổn định | Thấp | Thấp | Pydantic reject → 422 |

### E — Elevation of Privilege

| Mối đe dọa | Tài sản | Khả năng | Tác động | Giảm thiểu |
|---|---|---|---|---|
| IDOR đọc dữ liệu người khác | Result/Progress | TB | Cao | Ownership check repo; trả 404 (không xác nhận tồn tại) |
| **Counselor truy cập học sinh ngoài trường mình** | Dữ liệu HS | TB | **Cao** | RBAC theo school_id (CP-4); kiểm tra quan hệ counselor↔student |
| **Guardian xem dữ liệu trẻ không thuộc mình** | Dữ liệu trẻ | Thấp | Cao | Kiểm tra GuardianLink verified |
| **Bypass cổng consent để xử lý dữ liệu trẻ <16** | Tuân thủ pháp lý | TB | **Critical** | Consent Guard tập trung (CP-1); TLA+ chứng minh không đường vòng |
| Dùng token hết hạn | Auth | Thấp | TB | exp enforced |
| Injection qua nội dung nhập | Process | Rất thấp | Critical | CSP; Pydantic; no eval; parameterized SQL |

### ★ Mối đe dọa đặc thù AI/đạo đức (ngoài STRIDE cổ điển)

| Mối đe dọa | Tài sản | Giảm thiểu |
|---|---|---|
| **Gợi ý thiên lệch** theo giới/vùng/hoàn cảnh | Công bằng | **Bias testing** định kỳ (NFR-12); tài liệu hóa; RIASEC/MBTI không khóa cứng lựa chọn |
| **Ép buộc phân luồng** (tự động hóa quyết định) | Quyền tự quyết | Human-in-the-loop (CP-5); gợi ý + lý do; "không ép buộc" (TT 16/2026) |
| **Gợi ý không giải thích được** | Minh bạch AI | rationale NOT NULL (CP-6); Luật 134/2025 Đ.4 |
| Thao túng đầu vào để bóp méo gợi ý | Tính toàn vẹn | Validate input; rate limit; log input→reco→confirm |

---

## Điểm rủi ro DREAD (1–10)

| Mối đe dọa | D | R | E | A | D | Tổng | Ưu tiên |
|---|---|---|---|---|---|---|---|
| **Lộ kết quả trắc nghiệm (dữ liệu nhạy cảm)** | 9 | 6 | 6 | 9 | 6 | **36** | **Critical** |
| **Bypass cổng consent <16** | 9 | 6 | 6 | 8 | 6 | **35** | **Critical** |
| JWT spoofing qua lộ khóa | 10 | 7 | 8 | 8 | 6 | 39 | **Critical** |
| Giả mạo giám hộ cấp consent | 8 | 6 | 6 | 7 | 6 | 33 | **High** |
| Counselor vượt phạm vi trường | 7 | 7 | 5 | 7 | 7 | 33 | **High** |
| IDOR dữ liệu hướng nghiệp | 7 | 8 | 5 | 7 | 8 | 35 | **High** |
| Gợi ý thiên lệch (bias) | 6 | 6 | 5 | 9 | 5 | 31 | **High** |
| Credential stuffing | 8 | 7 | 7 | 8 | 6 | 36 | High |
| SQL injection | 10 | 4 | 8 | 5 | 4 | 31 | High |
| Refresh token replay | 9 | 4 | 5 | 5 | 5 | 28 | Medium |
| Email enumeration | 3 | 7 | 3 | 8 | 7 | 28 | Medium |

---

## Rủi ro tồn dư được chấp nhận

| Rủi ro | Lý do |
|---|---|
| Single node ở MVP | Đơn giản hóa MVP; HA ở giai đoạn sau (xem scalability) |
| Chưa tích hợp VNeID đầy đủ ở MVP | Xác thực giám hộ qua email ở MVP; VNeID tăng cường giai đoạn sau |
| Chưa 2FA/MFA | Giai đoạn sau; ưu tiên consent & dữ liệu nhạy cảm trước |
| Không audit READ dữ liệu **không nhạy cảm** | Quá ồn; **READ dữ liệu nhạy cảm thì BẮT BUỘC audit (CP-3)** |
| SQLite single-writer ở MVP | Chấp nhận ở quy mô MVP; lộ trình Postgres đã thiết kế |

> **Không chấp nhận** (phải xử lý trước phát hành): bất kỳ đường nào bypass Consent Guard, bất kỳ READ kết quả nhạy cảm không sinh audit, bất kỳ gợi ý thiếu rationale hoặc tự áp dụng không qua người. Đây là các CP bắt buộc + cần DPIA (spec.md Gate A/C).
