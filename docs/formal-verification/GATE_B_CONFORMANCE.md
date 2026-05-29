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

## Ý nghĩa & giới hạn (trung thực)
- ✅ Chứng minh **máy trạng thái consent của impl khớp ConsentLifecycle** (transition none↔active↔revoked đúng tiền điều kiện CP-1/CP-2). Impl không thực hiện transition nào spec cấm.
- ⚠️ **CP-1 phần artifact** (`ConsentInvariant` trên dữ liệu hướng nghiệp) **vacuous ở slice 1** vì chưa có route xử lý dữ liệu (`artifacts={}`). Sẽ exercisable ở **slice 2** khi `ProcessCareerData` có route thật (assessments) — lúc đó trace thêm event ProcessCareerData và invariant artifact mới có hiệu lực.
- ⚠️ Abstraction map (UUID→c1) là thủ công cho 1 trẻ; mở rộng đa-trẻ ở slice sau.
- ⏳ **AuthTokenLifecycle (CP-7)** conformance: cùng pattern, làm ở vòng tiếp (login=Issue/refresh=Rotate/logout=Logout). Chưa chạy lần này.

## Artifact
- Harness: `backend/app/core/trace.py` + hook ở `backend/app/guardians/service.py` (env-gated).
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
