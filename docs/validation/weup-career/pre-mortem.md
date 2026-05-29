# Pre-mortem — WeUp Career

> Phương pháp Klein (HBR 2007). Đổi khung: giả định ĐÃ thất bại, đi tìm vì sao. Tài liệu này gồm (a) hướng dẫn workshop để con người chạy, (b) **danh sách rủi ro hạt giống** đã phân tích sẵn để mồi thảo luận.

## A. Hướng dẫn workshop (con người chạy)
1. Triệu tập 4–8 bên: architect, SRE, security, PO, 1 đại diện trường (counselor), 1 phụ huynh/đại diện pháp chế.
2. Khung mở đầu: *"Hôm nay là tháng 11/2026. WeUp Career đã bị tuyên bố thất bại và đang bị gỡ bỏ. Vì sao?"*
3. Mỗi người viết im lặng 5–10 lý do (10 phút).
4. Round-robin chia sẻ, gom cụm lên bảng.
5. Bỏ phiếu top 5 rủi ro.
6. Mỗi rủi ro top: điều gì lẽ ra ngăn được, đã có trong thiết kế chưa? Nếu chưa → punch list.

## B. Rủi ro hạt giống (phân tích trước để mồi)

| ID | Kịch bản thất bại | Lẽ ra ngăn bằng | Có trong thiết kế? |
|---|---|---|---|
| **R1** | Kết quả trắc nghiệm của một trẻ <16 bị rò rỉ → khủng hoảng niềm tin + vi phạm BVDLCN | CP-1/CP-3, Field Crypto, no-PII-log, RBAC | ✅ Có (ADR-010/011, FF-01/03/04/05/10) |
| **R2** | Báo chí phát hiện gợi ý thiên lệch giới/vùng → mất uy tín, vi phạm Luật 134/2025 | Bias testing bắt buộc | ✅ **khung + CI wired** (`docs/testing/bias-testing.md`, P-1 đóng ở mức thiết kế); execution chờ engine |
| **R3** | Phụ huynh giả mạo đồng ý cho trẻ → xử lý dữ liệu trái phép | Xác thực giám hộ mạnh (VNeID) | ⚠️ **Một phần** — MVP chỉ email → **P-4** |
| **R4** | Lịch trình trượt vì các SPI không compose / [CRED_F30D5C6C] thật vượt SLO | Thin-slice spike falsify sớm | ❌ **Chưa** — spike blocked (chưa code) → **P-3** |
| **R5** | Không được phê duyệt vận hành vì thiếu DPIA / [CRED_FE4BE2F0] loại rủi ro AI | DPIA + hồ sơ rủi ro trước launch | ❌ **Chưa** → **P-2** |
| **R6** | Quá tải khi nhiều trường dùng đồng loạt; SQLite→Postgres migrate lỗi ở quy mô QG | Abstraction (ADR-002) + load test + spike | ⚠️ Thiết kế có abstraction; **chưa load-test ở quy mô** → P-3/P-6 |
| **R7** | Counselor xem nhầm học sinh trường khác → khiếu nại quyền riêng tư | RBAC theo school_id | ✅ Có (CP-4, FF-05) |
| **R8** | Nội dung không phù hợp lứa tuổi / [CRED_DC8AF1B4] cập nhật | Versioned + school_level + rà soát định kỳ | ✅ Có (FF-13/18) — cần quy trình rà soát vận hành |
| **R9** | Học sinh hiểu gợi ý là "phán quyết bắt buộc" → tổn thương tâm lý/ép buộc | Human-in-the-loop + ngôn ngữ "quyết định thuộc về bạn" + module NL4 | ✅ Có (CP-5, UX, wellbeing) — cần kiểm thử UX thực tế |

## C. Top rủi ro & trạng thái mitigation (đề xuất để workshop chốt)
1. **R2 (bias)** — mitigation tồn tại nhưng **chưa enforce** → ưu tiên P-1.
2. **R5 (DPIA/AI risk)** — bắt buộc pháp lý, chưa làm → P-2.
3. **R3 (giả mạo giám hộ)** — MVP yếu → P-4.
4. **R4/R6 (composition & scale chưa falsify)** → P-3 (spike + load test khi có khung impl).
5. **R9 (tác động tâm lý)** — thiết kế tốt nhưng cần UX research thực địa.

> R1, R7, R8 đã được thiết kế che phủ tốt (TLA+ + fitness). Trọng tâm hành động: **P-1, P-2, P-4** (làm được ngay) và **P-3** (khi có implementation).
