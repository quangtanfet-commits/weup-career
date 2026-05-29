# Evidence Pack — WeUp Career (validate-design)

**Ngày:** 2026-05-29 · **Proposal:** [`docs/spec.md`](../../spec.md) v2.0.0
**Nguyên tắc:** PO ký trên **evidence pack**, không phải trên prose. Pack chưa đầy đủ cho mọi method đã chọn ⇒ **chặn sign-off**.

---

## 1. Phân loại miền (Cynefin)

| Subsystem | Miền | Bằng chứng 1 câu |
|---|---|---|
| Cổng đồng ý giám hộ (grant/revoke/process) | **Complex** | hành vi nổi lên dưới interleaving grant↔revoke↔process trên nhiều user |
| Đọc dữ liệu nhạy cảm + audit | **Complex** | tính nguyên tử read+audit dưới truy cập đồng thời |
| Vòng đời token (xoay vòng) | **Complex** | cửa sổ hai-token-active dưới rotation đồng thời |
| Gợi ý AI (human-in-the-loop) | **Complicated** | máy trạng thái xác nhận; đúng đắn bằng inspection được |
| RBAC quan hệ (guardian/counselor) | **Adversarial** | có actor cố truy cập dữ liệu ngoài quyền |
| Dữ liệu trẻ <16 / [CRED_F931E5D8] giám hộ | **Adversarial** | kẻ tấn công giả mạo giám hộ / [CRED_4A57BC7D] consent |
| Công bằng/thiên lệch thuật toán gợi ý | **Adversarial + Complicated** | bias không lộ qua inspection; cần kiểm thử |
| Tiến bộ năng lực K-A-R | **Simple** | đơn điệu, kiểm tra cơ học |
| Lời hứa cấu trúc (hexagonal, mã hóa, no-PII-log, ownership) | **Simple** | mệnh đề cơ học, fitness-checkable |

## 2. Selection rubric → **FULL PACK**

Cả 4 điều kiện đều thỏa (concurrent protocol ✅ · attacker-controlled surface ✅ · cắt ngang >2 service ✅ · nhiều structural claim ✅) ⇒ chạy full pack.

| # | Method (yield-per-effort) | Trạng thái | Artifact |
|---|---|---|---|
| 1 | **TLA+ model checking** (Level 5) | ✅ **DONE** | [`../../formal-verification/TLC_REPORT.md`](../../formal-verification/TLC_REPORT.md) · [`tla/`](../../../tla/) — 6 module CP-1…CP-8, 6/6 sabotage |
| 2 | **Fitness functions** (Level 8) | ✅ catalogue lập | [`fitness-functions.md`](./fitness-functions.md) |
| 3 | **Threat model + attack trees** | ✅ STRIDE done, attack trees thêm | [`threat-model.md`](./threat-model.md) (+ [`../../security/threat-model.md`](../../security/threat-model.md)) |
| 4 | **Pre-mortem** | ✅ materials + seeded risks | [`pre-mortem.md`](./pre-mortem.md) |
| 5 | **Thin-slice spike** (Level 6) | ⛔ **BLOCKED** — chưa có implementation | [`spike-report.md`](./spike-report.md) (kế hoạch + time-budget) |

## 3. Punch list (chặn sign-off đến khi xử lý)

| ID | Rủi ro/Gap | Nguồn | Hành động |
|---|---|---|---|
| P-1 | **Bias-test** — ✅ khung thiết kế ([`../../testing/bias-testing.md`](../../testing/bias-testing.md)) + job CI `bias-test` wired (path-filtered, không fake-pass). Execution chờ Recommendation Engine | pre-mortem R2, fitness FF-11 | Chạy suite khi có engine |
| P-2 | **DPIA** — ✅ bản thảo đã soạn ([`../../legal/dpia.md`](../../legal/dpia.md)). Còn: thông báo rủi ro AI→Bộ KH&CN (P-2b), rà soát pháp chế (D-4) | pre-mortem R5 | Đóng P-2b/D-4 trước phát hành |
| P-3 | **Thin-slice spike chưa chạy** — SPI composition & latency chưa được falsify | method 5 | Chạy spike 4–6 ngày khi có khung impl |
| P-4 | **Xác thực giám hộ** — ✅ thiết kế luồng VNeID phân tầng ([`../../security/guardian-verification.md`](../../security/guardian-verification.md)): HIGH/MEDIUM/LOW; dữ liệu nhạy cảm trẻ <16 cần ≥MEDIUM (FF-19). Execution chờ tích hợp VNeID thật (thủ tục C06) | threat-model B3.1 | Đăng ký tích hợp C06 + code |
| P-5 | **Gate B (conformance)** — ✅ PASS slice-1 cho ConsentLifecycle (CP-1/CP-2): trace thật replay qua TLA+, sabotage xác nhận có răng ([`../../formal-verification/GATE_B_CONFORMANCE.md`](../../formal-verification/GATE_B_CONFORMANCE.md)). Mở rộng: CP-1 artifact + CP-7 token + đa-trẻ theo slice | TLC report | Mở rộng theo slice |

## 4. Verdict
**Sign-off: CHƯA.** Bằng chứng cấp cao (TLA+, threat model, fitness catalogue, pre-mortem) đã mạnh, nhưng punch list P-1…P-5 phải đóng. P-3/P-5 phụ thuộc implementation; P-1/P-2/P-4 làm được ngay ở giai đoạn thiết kế.
