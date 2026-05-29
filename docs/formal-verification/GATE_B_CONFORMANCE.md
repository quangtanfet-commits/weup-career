# Gate B — Conformance Report (slice 1) — WeUp Career

**Ngày:** 2026-05-29 · **Phạm vi:** ConsentLifecycle (CP-1/CP-2) · **Branch:** `feat/phase1-auth-consent`
**Công cụ:** TLC trace-validation (Specula `tracedebugger`) + CommunityModules (Json/IOUtils)

> Gate A (model check) chứng minh **spec đúng**; **Gate B chứng minh IMPL khớp spec** (không drift) — formal-verify Hard Rule 7. Đây là Gate B đầu tiên, cho lõi pháp lý consent.

---

## Cách làm
1. **Instrument** (in-code, env-gated): `app/core/trace.py` — `emit(event, user, state)` ghi 1 dòng NDJSON/transition khi `WEUP_TRACE_FILE` set; **no-op** khi không set (100 test cũ vẫn pass). Hook tại `GuardianService.grant_consent` → `GrantConsent`, `revoke_consent` → `RevokeConsent`.
2. **Sinh trace thật**: drive app chạy thật (uvicorn + sqlite) qua chuỗi register<16 → invite → grant → revoke → grant. Map UUID trẻ → `c1` (abstraction map). Trace: `tla/trace/consent_trace.ndjson`.
3. **Replay** qua `tla/trace/ConsentTrace.tla` (EXTENDS `ConsentTraceBase` + Json/IOUtils) — mỗi bước impl phải là transition **enabled** trong spec đã verify + post-state khớp log. Convention Specula: TLC "Deadlock" khi `l > Len(trace)` = **tiêu thụ hết trace = THÀNH CÔNG**.

## Kết quả

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[Grant, Revoke, Grant]` (thật từ impl) | Deadlock @ State 4, **l=4 (=Len+1)** | ✅ Tiêu thụ HẾT trace; c1: none→active→revoked→active; mọi bước enabled; post-state khớp; 0 vi phạm invariant → **IMPL CONFORM** |
| **Sabotage** | `[Grant, Grant]` (double-grant — spec cấm) | Deadlock @ State 2, **l=2 (=Len, KHÔNG đạt Len+1)** | ✅ Event #2 KHÔNG tiêu thụ được (`GrantConsent` khi `consent=active` không enabled) → **drift bị bắt** |

**Discriminator:** conform ⇔ `l` đạt `Len+1`. Good trace `l→4`; bad trace kẹt `l=2`. Check có răng (không always-green).

## Mở rộng slice 2 — CP-1 artifact conformance (✅ đã đóng caveat)

Slice 2 (assessments) emit thêm event `ProcessCareerData` ở submit → `ConsentInvariant` (CP-1) giờ **NON-vacuous**.

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[GrantConsent, ProcessCareerData]` (thật) | Deadlock @ State 3, **l=3 (=Len+1)** | ✅ Tiêu thụ hết; State 3 `artifacts={[owner|->c1, consentAtCreation|->"active"]}` — **artifacts KHÁC RỖNG**; `ConsentInvariant` được kiểm thật & giữ → impl chỉ tạo artifact khi consent active |
| **Sabotage** | `[ProcessCareerData]` (chưa Grant, consent=none) | Deadlock @ State 1, **l=1 (≠Len+1)** | ✅ Event không tiêu thụ được (`ProcessCareerData` yêu cầu `CanProcess`=consent active) → drift bị bắt; khớp CP-1 gate (submit 403 khi chưa consent) |

`TraceProcess` trong `ConsentTrace.tla` validate `[owner, consentAtCreation] \in artifacts'`.

> ⚠️ **Giới hạn trung thực:** emit ở submit hardcode `consentAtCreation="active"` (vì submit chỉ tới được sau khi qua CP-1 gate). Negative-case (process khi chưa consent) **được chặn bởi gate**, kiểm riêng bằng holdout CP-1 (403/201) + sabotage trace ở trên — không dựa vào giá trị state trong emit.

## Mở rộng slice 3 — CP-8 competency progress conformance (✅)

Slice 3 emit `AdvanceDepth {competency, depth(rank)}` khi nâng độ sâu. Spec: `CompetencyProgressTrace.tla` + `CompetencyProgressTraceBase.tla` (`Advance` chỉ enabled khi rank mới > hiện tại).

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[AdvanceDepth 1, 2, 3]` cho (l1,c1) (thật, NL10 K→A→R) | Deadlock @ State 4, **l=4 (=Len+1)** | ✅ Tiêu thụ hết; depth 0→1→2→3, **mỗi bước tăng ngặt** → CP-8 monotonic giữ trên impl |
| **Sabotage** | `[AdvanceDepth 3, AdvanceDepth 1]` (giảm) | Deadlock @ State 2, **l=2 (≠Len+1)** | ✅ Bước giảm không enabled (1 không > 3) → drift bị bắt |

> Nhất quán với holdout S3: impl chỉ emit `AdvanceDepth` (và chỉ ghi `learner_progress`) khi độ sâu THỰC SỰ tiến; lần không tiến → không sự kiện, không drift. CP-8 (monotonic + append-only) giữ.

## Ý nghĩa & giới hạn (trung thực)
- ✅ Chứng minh **máy trạng thái consent của impl khớp ConsentLifecycle** (transition none↔active↔revoked + ProcessCareerData đúng tiền điều kiện CP-1/CP-2). Impl không thực hiện transition nào spec cấm.
- ✅ **CP-1 phần artifact giờ NON-vacuous** (slice 2) — xem mục mở rộng trên.
- ⚠️ Abstraction map (UUID→c1) là thủ công cho 1 trẻ; mở rộng đa-trẻ ở slice sau.
- ✅ **AuthTokenLifecycle (CP-7)** conformance: đã chạy — xem mục dưới.

## Mở rộng — CP-7 token lifecycle conformance (✅)

Instrument `AuthService`: login→`Issue`, refresh→`Rotate`, logout→`Logout` (env-gated; `token_label()` map hash→t1/t2/… process-lifetime). Spec: `AuthTokenTrace.tla` + `AuthTokenTraceBase.tla`.

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[Issue t1, Rotate t1→t2, Rotate t2→t3, Logout t3]` (thật) | Deadlock @ State 5, **l=5 (=Len+1)** | ✅ Tiêu thụ hết; `AtMostOneActiveToken` giữ ở MỌI state — rotation **nguyên tử**, không bao giờ 2 token active cùng lúc (CP-7) |
| **Sabotage** | `[Issue t1, Issue t2]` (2 active, không rotate) | Deadlock @ State 2, **l=2 (≠Len+1)** | ✅ Issue thứ 2 không enabled (đã có active) → drift bị bắt |

> ⚠️ **Ranh giới trừu tượng (trung thực):** spec mô hình **MỘT phiên** (`AtMostOneActiveToken` = ≤1 active/user). Impl thực tế **cho ĐA phiên** (login nhiều thiết bị = nhiều refresh token active — đúng thiết kế). Conformance này chứng minh **tính nguyên tử của rotation + revoke trong MỘT phiên** (bản chất an toàn CP-7). Đa-phiên ngoài phạm vi model hiện tại (nâng spec → per-session active set nếu cần). Chống tái dùng token thu hồi đã được holdout A4 phủ (reuse RT cũ → 401).

## Mở rộng slice 5 — CP-5/CP-6 recommendation governance conformance (✅)

Instrument `RecoService`: `generate()`→`RecommendationCreated`, `confirm()`→`RecommendationConfirmed` (env-gated). Spec: `RecommendationTrace.tla` + `RecommendationTraceBase.tla` (bản trace-friendly của `RecommendationGovernance`, RecIds/Humans literal). Trace từ app thật: register(≥16)→submit RIASEC→`POST /recommendations`→`POST /{id}/confirm`; UUID reco/user relabel → r1/u1.

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[RecommendationCreated r1, RecommendationConfirmed r1 by u1=accepted]` (thật) | Deadlock @ State 3, **l=3 (=Len+1)** | ✅ Tiêu thụ hết; `RationaleAlways` (CP-6) + `HumanInTheLoop` (CP-5) giữ ở MỌI state — gợi ý tạo ra luôn có rationale, chỉ thành "accepted" SAU khi con người (u1) xác nhận |
| **Sabotage** | `[RecommendationConfirmed r1]` (confirm khi chưa create) | Deadlock @ State 1, **l=1 (≠Len+1)** | ✅ `Confirm` không enabled (status≠"proposed") → drift bị bắt; impl không có đường nào confirm một gợi ý chưa tồn tại |

> Gate A song hành: `RecommendationGovernanceMC` = "Model checking completed. No error" (64 distinct states); `RecommendationGovernanceSab` = "Invariant **HumanInTheLoop** is violated" (gỡ guard con-người → bị bắt). CP-5/CP-6 đều non-vacuous ở cả hai gate.
>
> Bias (M1–M5) là gate ĐỘC LẬP (`tests/bias/`, Luật 134/2025) — TLC chứng minh *quy trình* human-in-the-loop, KHÔNG chứng minh gợi ý *công bằng*. Sabotage-check bias: inject engine biased thật → M2/M3/M4/M5 đều FAIL ⇒ suite có teeth (đóng P-1).

## Artifact
- Harness: `backend/app/core/trace.py` (emit + token_label; emit loại key `None` để JSON parse được trong TLA) + hook ở `backend/app/guardians/service.py`, `backend/app/assessments/service.py`, `backend/app/auth/service.py`, `backend/app/reco/service.py` (env-gated).
- Token spec: `tla/trace/AuthTokenTrace.tla`, `AuthTokenTraceBase.tla`, `AuthTokenTrace.cfg`, `token_trace.ndjson`.
- Reco spec: `tla/trace/RecommendationTrace.tla`, `RecommendationTraceBase.tla`, `RecommendationTrace.cfg`, `recommendation_trace.ndjson`.
- Spec: `tla/trace/ConsentTrace.tla`, `ConsentTraceBase.tla`, `ConsentTrace.cfg`.
- Trace: `tla/trace/consent_trace.ndjson`.

## Cách chạy lại
```bash
# 1. Sinh trace: boot app với WEUP_TRACE_FILE rồi chạy grant/revoke/grant; map UUID→c1.
# 2. Validate:
#    MCP tracedebugger.run_trace_validation(
#      spec=ConsentTrace.tla, cfg=ConsentTrace.cfg, trace=consent_trace.ndjson,
#      work_dir=tla/trace, community_jar=/opt/specula/lib/CommunityModules-deps.jar)
#    → kỳ vọng: Deadlock với l=Len+1 (tiêu thụ hết).
```

> **Verdict slice 1:** Gate B **PASS** cho ConsentLifecycle (CP-1/CP-2 transition conformance) + sabotage xác nhận. Đóng **P-5** ở mức slice-1; mở rộng (CP-1 artifact, CP-7 token, đa-trẻ) theo slice.
