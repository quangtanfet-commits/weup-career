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

## Mở rộng slice 6 — CP-4 relational RBAC (Gate A + integration)

> **Cập nhật 2026-05-31:** slice 6 ban đầu phủ CP-4 bằng Gate A + integration. Slice 7 (dưới) **bổ sung trace harness thời gian** cho CP-4 (và CP-3) — conformance giờ có harness replay riêng, không chỉ dựa integration. Phần dưới giữ nguyên làm bối cảnh.

CP-4 (counselor↔student, guardian↔child ownership) là **predicate phân quyền** (truy vấn quan hệ tại từng request), KHÔNG phải máy trạng thái thời gian như consent/token/reco. Vì vậy:
- **Gate A** — `AuthorizationModelMC`: "Model checking completed. No error" (128 distinct states, `OwnershipInvariant` giữ). `AuthorizationModelSab`: "Invariant **OwnershipInvariant** is violated" (cấp quyền cross-relation → bị bắt; teeth).
- **Conformance** phủ bởi integration trên app thật (không cần trace harness thời gian): counselor cùng trường đọc được học sinh được phân công; **khác trường → 404**; class-scope; counselor đọc dữ liệu nhạy cảm → **de-sensitized** (không payload thô) + **1 CP-3 audit**; **G-6** giám hộ verified xem + confirm reco của trẻ (confirmed_by=người thật, unrelated→404) — tái dùng `RecommendationConfirmed` trace của Gate B slice 5.

## Mở rộng slice 7 — CP-3 SensitiveDataAccess + CP-4 AuthorizationModel trace harness (✅ đạt 6/6)

Một emit thật `CounselorReadStudent` (tại `app/school/service.py`, bắn SAU khi `_can_access` qua + đúng 1 audit nhạy cảm được ghi) drive **CẢ HAI** CP từ hai góc. Sinh trace thật bằng pytest qua ASGI app + sqlite: cùng 1 counselor đọc cùng 1 student 3 lần; relabel UUID counselor→`co1`, student→`s1`. Trace dùng chung: `sensitive_read_trace.ndjson`.

**CP-3 — SensitiveDataAccess** (`SensitiveDataAccessTrace.tla` + `…Base.tla`, counter `reads`/`audits`, `ReadSensitive` tăng song song; `AuditCompleteness == reads = audits`):

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[Read, Read, Read]` (thật, sensitiveAccess=TRUE) | Deadlock @ State 4, **l=4 (=Len+1)** | ✅ Tiêu thụ hết; mỗi đọc nhạy cảm → đúng 1 audit (`reads=audits=3`); `AuditCompleteness` giữ ở MỌI state → CP-3 không bao giờ đọc thiếu/thừa audit |
| **Sabotage** | `[Read(TRUE), Read(FALSE)]` (`sensitive_read_sabotage.ndjson`) | Deadlock @ State 2, **l=2 (≠Len+1)** | ✅ Event #2 không tiêu thụ (`TraceRead` yêu cầu `sensitiveAccess=TRUE`) → drift bị bắt |

**CP-4 — AuthorizationModel** (`AuthorizationModelTrace.tla` + `…Base.tla`, `CanAccess` giữ nguyên cấu trúc vị từ spec đã verify; `CounselorOf = {<<co1,s1>>}`; `OwnershipInvariant == \A g \in grants : CanAccess(g[1],g[2])`):

| Run | Trace | Kết quả TLC | Diễn giải |
|---|---|---|---|
| **Conformance** | `[co1→s1, co1→s1, co1→s1]` (thật) | Deadlock @ State 4, **l=4 (=Len+1)** | ✅ Tiêu thụ hết; mỗi `Access` chỉ enabled khi `CanAccess` (co1 được phân công s1); `OwnershipInvariant` giữ → impl không cấp quyền đọc vượt quan hệ phân công |
| **Sabotage** | `[co1→s1, s1→co1]` (`authorization_sabotage.ndjson`, s1 đọc co1 — không phân công) | Deadlock @ State 2, **l=2 (≠Len+1)** | ✅ Event #2 không tiêu thụ (`CanAccess(s1,co1)`=FALSE) → drift bị bắt |

> Discriminator nhất quán: conform ⇔ `l` đạt `Len+1=4`; cả hai sabotage kẹt `l=2`. Cùng một trace thật được validate từ hai vị từ độc lập (đếm audit CP-3 + quan hệ phân quyền CP-4) — chặt hơn "CP-4 = chỉ Gate A + integration" của slice 6.

**Verdict 6/6:** mọi module trong spec-pack giờ có conformance trace replay + sabotage teeth — ConsentLifecycle (CP-1/CP-2), CompetencyProgress (CP-8), AuthTokenLifecycle (CP-7), RecommendationGovernance (CP-5/CP-6), **SensitiveDataAccess (CP-3)**, **AuthorizationModel (CP-4)**.

## Artifact
- Harness: `backend/app/core/trace.py` (emit + token_label; emit loại key `None` để JSON parse được trong TLA) + hook ở `backend/app/guardians/service.py`, `backend/app/assessments/service.py`, `backend/app/auth/service.py`, `backend/app/reco/service.py`, `backend/app/school/service.py` (env-gated).
- Token spec: `tla/trace/AuthTokenTrace.tla`, `AuthTokenTraceBase.tla`, `AuthTokenTrace.cfg`, `token_trace.ndjson`.
- Reco spec: `tla/trace/RecommendationTrace.tla`, `RecommendationTraceBase.tla`, `RecommendationTrace.cfg`, `recommendation_trace.ndjson`.
- Consent spec: `tla/trace/ConsentTrace.tla`, `ConsentTraceBase.tla`, `ConsentTrace.cfg`, `consent_trace.ndjson`, `consent_artifact_trace.ndjson`.
- Competency spec: `tla/trace/CompetencyProgressTrace.tla`, `CompetencyProgressTraceBase.tla`, `CompetencyProgressTrace.cfg`, `competency_trace.ndjson`.
- **SensitiveData spec (CP-3, slice 7):** `tla/trace/SensitiveDataAccessTrace.tla`, `SensitiveDataAccessTraceBase.tla`, `SensitiveDataAccessTrace.cfg`.
- **Authorization spec (CP-4, slice 7):** `tla/trace/AuthorizationModelTrace.tla`, `AuthorizationModelTraceBase.tla`, `AuthorizationModelTrace.cfg`.
- **Trace dùng chung CP-3/CP-4:** `tla/trace/sensitive_read_trace.ndjson` (thật, relabel co1/s1); sabotage: `sensitive_read_sabotage.ndjson`, `authorization_sabotage.ndjson`.

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
>
> **Verdict tổng (2026-05-31):** Gate B **6/6** — mọi module spec-pack có conformance trace replay + sabotage teeth (CP-1…CP-8 đều phủ). Không module nào chỉ còn "Gate A + integration".
