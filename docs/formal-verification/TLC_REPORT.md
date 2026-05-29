# TLC Verification Report — WeUp Career

**Ngày:** 2026-05-29 · **Công cụ:** TLA+ tla2tools (TLC), Java 21 · **Spec-pack:** [`tla/`](../../tla/)
**Phạm vi:** 6 module ↔ 8 thuộc tính đúng đắn CP-1…CP-8 ([`docs/spec.md`](../spec.md) §8, thiết kế: [`tla-spec-design.md`](./tla-spec-design.md)).

> **Gate A (model check) + sabotage-check: HOÀN TẤT.** Gate B (conformance trace replay) **chưa chạy** — chưa có implementation (`backend/app/`). Sẽ kích hoạt khi có code (xem §Gate B).

---

## Kết quả Gate A (model check)

| Module | CP | Invariant/Property | Distinct states | Depth | Kết quả |
|---|---|---|---:|---:|---|
| `ConsentLifecycle` | CP-1, CP-2 | `ConsentInvariant`, `NoRevokedProcessing` | 50 | 8 | ✅ No error |
| `SensitiveDataAccess` | CP-3 | `AuditCompleteness` | 6 | 6 | ✅ No error |
| `AuthorizationModel` | CP-4 | `OwnershipInvariant` | 128 | — | ✅ No error |
| `RecommendationGovernance` | CP-5, CP-6 | `HumanInTheLoop`, `RationaleAlways` | 64 | 5 | ✅ No error |
| `AuthTokenLifecycle` | CP-7 | `AtMostOneActiveToken` | 201 | 7 | ✅ No error |
| `CompetencyProgress` | CP-8 | `Monotone` (action property) | 256 | 5 | ✅ No error |

Tất cả khám phá **hết không gian trạng thái** trong model bị chặn (0 state left on queue). Xác suất trùng fingerprint ~5×10⁻¹⁶ (mô hình nhỏ).

## Sabotage-check (hard rule — "TLC pass với invariant yếu = THẤT BẠI")

Với mỗi invariant, phá **một** guard/hành động trong spec; TLC **phải** báo vi phạm. Nếu vẫn xanh ⇒ invariant quá yếu.

| Module sabotage | Phá điều gì | Kết quả TLC | Đủ mạnh? |
|---|---|---|---|
| `ConsentLifecycleSab` | Bỏ guard `CanProcess` | `ConsentInvariant is violated` @ State 2 (`ProcessCareerData("c1")`) | ✅ |
| `SensitiveDataAccessSab` | Đọc không ghi audit | `AuditCompleteness is violated` | ✅ |
| `AuthorizationModelSab` | Bỏ guard `CanAccess` | `OwnershipInvariant is violated` | ✅ |
| `RecommendationGovernanceSab` | `AutoApply` tự accept không cần người | `HumanInTheLoop is violated` | ✅ |
| `AuthTokenLifecycleSab` | `BadRotate` không revoke token cũ | `AtMostOneActiveToken is violated` | ✅ |
| `CompetencyProgressSab` | Cho phép `Decrease` độ sâu | `Monotone is violated` | ✅ |

**6/6 sabotage báo vi phạm đúng kỳ vọng** → mọi invariant đều load-bearing, không tautology.

## Model constants (vì sao kích thước này)

| Module | Constants | Lý do |
|---|---|---|
| ConsentLifecycle | Users={c1,c2,a1}, AgeBand: 2×under_16 + 1×ok | ≥2 trẻ để phơi bày khác biệt; 1 người ≥16 để kiểm nhánh không-cần-consent |
| SensitiveDataAccess | MaxReads=5 | đủ để đếm lệch read/audit nếu có |
| AuthorizationModel | 5 subjects: student+guardian+counselor cùng/khác trường | phơi bày truy cập chéo (counselor↔trường khác, guardian↔trẻ khác) |
| RecommendationGovernance | RecIds={r1,r2}, Humans={student,guardian} | ≥2 rec, ≥2 người xác nhận |
| AuthTokenLifecycle | TokenIds={t1,t2,t3}, AppUsers={u1,u2} | ≥3 token để xoay vòng + ≥2 user kiểm "1 active/user" |
| CompetencyProgress | Learners={l1,l2}, Comps={NL1,NL10} | ≥2 learner × ≥2 năng lực; độ sâu 0..3 |

## Ghi chú phạm vi & trung thực

- **Tính chất đã kiểm là SAFETY** (CP-1…CP-8 đều dạng "không điều xấu xảy ra"). Đúng bản chất các ràng buộc pháp lý.
- **Liveness/fairness chưa mô hình hóa** (vd "mọi gợi ý cuối cùng được xử lý"): chưa cần ở giai đoạn này vì các CP là safety; sẽ bổ sung khi mô hình hóa retry/queue (nếu có) theo `/formal-verify` mandatory coverage.
- **CP-2** được bao bởi `ConsentLifecycle` ở dạng safety (`NoRevokedProcessing` + `ConsentInvariant`): không artifact nào tạo ra khi consent="revoked".

## Gate B — Conformance (CHƯA chạy, blocking khi có code)

Khi `backend/app/` tồn tại:
1. Instrument source emit NDJSON trace mỗi action (harness — `/specula` `harness-generation`).
2. Viết `*Trace.tla` replay trace, assert mỗi bước enabled trong spec gốc.
3. Replay ≥1.000 trace từ test thật; mọi trace phải được chấp nhận.
4. Property-based test (Hypothesis) sinh chuỗi action ngẫu nhiên chạy qua impl.
5. CI: TLC (Gate A) + conformance (Gate B) chặn merge khi đổi state machine consent/reco/auth/progress (đã có khung `.github/workflows/ci.yml`).

## Cách chạy lại
```bash
JAR=/usr/local/share/tla/tla2tools.jar
cd tla
for m in ConsentLifecycle SensitiveDataAccess AuthorizationModel \
         RecommendationGovernance AuthTokenLifecycle CompetencyProgress; do
  java -cp $JAR tlc2.TLC -config "$m.cfg" "${m}MC.tla"
done
# Sabotage (kỳ vọng vi phạm):
for s in ConsentLifecycle SensitiveDataAccess AuthorizationModel \
         RecommendationGovernance AuthTokenLifecycle CompetencyProgress; do
  java -cp $JAR tlc2.TLC -config "${s}Sab.cfg" "${s}Sab.tla"
done
```
