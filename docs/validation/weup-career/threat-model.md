# Threat Model — Attack Trees (validate-design) — WeUp Career

> Bổ sung **attack trees** cho các bề mặt đối kháng then chốt, nối tiếp STRIDE/DREAD ở [`docs/security/threat-model.md`](../../security/threat-model.md). Mỗi lá gắn **mitigation** (trong thiết kế) hoặc **GAP** (vào punch list). Không lá nào để "TBD".

---

## Surface A — Lấy cắp kết quả trắc nghiệm của trẻ <16 (dữ liệu nhạy cảm)

```
GOAL A: Đọc trộm AssessmentResult của một trẻ <16
├── A1. Truy cập trực tiếp DB
│     ├── A1.1 Dump file DB ........... mitig: volume owned appuser; secrets (ADR-008)
│     └── A1.2 Đọc cột result_payload . mitig: Field Crypto mã hóa at-rest (ADR-011, FF-04)
├── A2. Qua API
│     ├── A2.1 IDOR đọc id người khác .. mitig: ownership→404 (CP-4, FF-05)
│     ├── A2.2 Counselor ngoài trường .. mitig: RBAC school_id (CP-4, FF-05)
│     └── A2.3 Giả token .............. mitig: JWT HS256 + exp (CP-7, FF-08)
├── A3. Qua kênh phụ
│     ├── A3.1 Đọc trong log .......... mitig: no-PII-log (FF-10); chỉ log metadata
│     ├── A3.2 Cache client/CDN ....... mitig: không cache dữ liệu nhạy cảm (ADR-004)
│     └── A3.3 Payload message bus ..... mitig: event chỉ mang id/loại (scalability)
└── A4. Suy luận gián tiếp
      └── A4.1 Đọc lý do gợi ý ......... mitig: rationale không lộ kết quả thô (tối thiểu hóa) — ⚠ kiểm tra khi viết engine
```

## Surface B — Bypass cổng đồng ý để xử lý dữ liệu trẻ <16

```
GOAL B: Xử lý dữ liệu hướng nghiệp của trẻ <16 KHÔNG có consent active
├── B1. Đường vòng qua route khác ..... mitig: Consent Guard ở tầng router cho MỌI route career-data (ADR-010); TLA+ chứng minh không đường vòng (CP-1)
├── B2. Tự đồng ý (self-consent) ...... mitig: cấm self-consent; GuardianLink phải verified qua kênh độc lập (ADR-010)
├── B3. Giả mạo người giám hộ
│     ├── B3.1 Đăng ký email giả làm GH . mitig: ✅ luồng VNeID phân tầng — quan hệ do CSDL dân cư khẳng định, dữ liệu nhạy cảm cần ≥MEDIUM (guardian-verification.md, FF-19); execution chờ tích hợp C06
│     └── B3.2 Chiếm email giám hộ ...... mitig: ngoài phạm vi app; khuyến nghị VNeID
└── B4. Claim JWT cũ sau khi revoke .... mitig: route nhạy cảm xác thực lại consent với DB (ADR-008); claim tối đa cũ 15'
```

## Surface C — Truy cập chéo tenant/trường (đa người dùng B2B2C)

```
GOAL C: Truy cập dữ liệu học sinh ngoài quyền
├── C1. Counselor → học sinh trường khác . mitig: RBAC theo school_id (CP-4, FF-05)
├── C2. School_admin → dữ liệu nhạy cảm chi tiết . mitig: admin quản trị, không xem payload nhạy cảm (auth-design RBAC)
├── C3. Guardian → trẻ chưa liên kết .... mitig: kiểm tra GuardianLink verified (CP-4, FF-05)
└── C4. Leo thang vai trò ............... mitig: tài khoản counselor/admin cấp qua school_admin; không tự nâng quyền
```

## Surface D — Thao túng/thiên lệch gợi ý AI (đối kháng đạo đức)

```
GOAL D: Khiến hệ thống đưa gợi ý sai lệch/ép buộc
├── D1. Bias hệ thống theo giới/vùng .... mitig: bias testing — ⚠ **GAP P-1** (CI job chưa có)
├── D2. Ép phân luồng tự động ........... mitig: human-in-the-loop, không auto-apply (CP-5, FF-07)
├── D3. Gợi ý không giải thích được ..... mitig: rationale NOT NULL (CP-6, FF-06)
└── D4. Thao túng input để bóp méo ...... mitig: validate input; rate limit; lưu vết input→reco→confirm
```

## Bản đồ mitigation → fitness function
Hầu hết lá đã chuyển thành FF (xem [`fitness-functions.md`](./fitness-functions.md)): A1.2→FF-04, A2.*→FF-05/FF-08, A3.1→FF-10, B1/B2→FF-01/FF-02, C*→FF-05, D1→FF-11(GAP), D2→FF-07, D3→FF-06.

## GAP (vào punch list README)
- ~~**P-4**: B3.1~~ → ✅ **đã thiết kế** luồng VNeID phân tầng (`docs/security/guardian-verification.md`); còn execution (tích hợp C06).
- ~~**P-1**: D1~~ → ✅ **đã thiết kế** khung bias-testing + CI wired (`docs/testing/bias-testing.md`); còn execution (chờ engine).
- ⚠ A4.1 — khi xây Recommendation Engine, kiểm tra rationale không rò rỉ kết quả nhạy cảm thô.
