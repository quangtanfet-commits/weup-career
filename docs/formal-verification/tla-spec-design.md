# Thiết kế Kiểm chứng Hình thức: Đặc tả TLA+/TLC — WeUp Career

**Phiên bản:** 2.0.0 | **Ngày:** 2026-05-29
**Thay thế:** v1.0.0 (mô hình Todo — placeholder, đã loại bỏ)
**Phạm vi:** Vòng đời đồng ý giám hộ (<16), truy cập dữ liệu nhạy cảm, mô hình phân quyền, quản trị gợi ý AI (human-in-the-loop), vòng đời token, tiến bộ năng lực K-A-R

> **Quy ước:** Văn xuôi tiếng Việt, định danh kỹ thuật tiếng Anh. Các đoạn TLA+ là **minh họa thiết kế** (sẽ được hiện thực hóa thành module `.tla`/`.cfg` đầy đủ trong `tla/`).
>
> **Nguồn ràng buộc:** mỗi module hiện thực hóa một/nhiều **thuộc tính đúng đắn (CP-1…CP-8)** trong [`docs/spec.md` §8](../spec.md), bắt nguồn từ [`docs/legal/legal-basis.md`](../legal/legal-basis.md) (§4.5, §6, §7). Đây là các bất biến **pháp lý**, không chỉ kỹ thuật — vi phạm = sản phẩm không được phép vận hành.

---

## Tổng quan

Tài liệu đặc tả các module TLA+ cần viết & kiểm chứng bằng TLC **trước khi triển khai production**. Đặc tả phục vụ:
1. Tham chiếu đúng đắn không nhập nhằng cho hiện thực.
2. Artifact kiểm chứng chứng minh các thuộc tính an toàn (safety) & sống còn (liveness) **bắt buộc theo luật**.
3. Tài liệu không trôi dạt khỏi ý định (khác tài liệu văn xuôi).

### Bản đồ Module ↔ Thuộc tính đúng đắn (spec.md §8)

| Module | Thuộc tính (CP) | Bản chất |
|---|---|---|
| 1. `ConsentLifecycle` | **CP-1, CP-2** | Không xử lý dữ liệu hướng nghiệp của trẻ <16 khi chưa/không còn đồng ý giám hộ |
| 2. `SensitiveDataAccess` | **CP-3** | Mọi lần đọc kết quả trắc nghiệm sinh đúng 1 audit log |
| 3. `AuthorizationModel` | **CP-4** | Không truy cập chéo trừ quan hệ được cấp quyền |
| 4. `RecommendationGovernance` | **CP-5, CP-6** | Human-in-the-loop + gợi ý luôn có lý do |
| 5. `AuthTokenLifecycle` | **CP-7** | Token thu hồi không tái sử dụng được; xoay vòng nguyên tử |
| 6. `CompetencyProgress` | **CP-8** | Tiến bộ K→A→R đơn điệu, lịch sử bất biến |

---

## Module 1: ConsentLifecycle (CP-1, CP-2) — bất biến pháp lý quan trọng nhất

### Mục đích
Mô hình vòng đời tài khoản trẻ <16 và đồng ý của người giám hộ; chứng minh **không có chuỗi thao tác nào** dẫn tới việc hệ thống xử lý/sinh dữ liệu hướng nghiệp cho trẻ <16 khi không có `GuardianConsent` ở trạng thái `active`.

### Tham số & biến trạng thái
```tla
CONSTANTS
  Users,              \* {"c1", "c2", "a1"} — c* trẻ <16, a* người ≥16
  AgeBand             \* [Users -> {"under_16", "ok"}]

VARIABLES
  consent,            \* [Users -> {"none", "active", "revoked"}]
  artifacts           \* Tập bản ghi dữ liệu hướng nghiệp đã sinh:
                      \*   [owner |-> Users, consentAtCreation |-> {"active","na"}]
```

### Bất biến kiểu & điều kiện xử lý
```tla
TypeInvariant ==
  /\ consent \in [Users -> {"none", "active", "revoked"}]
  /\ artifacts \subseteq [owner: Users, consentAtCreation: {"active","na"}]

\* Điều kiện ĐƯỢC PHÉP xử lý dữ liệu hướng nghiệp cho một user
CanProcess(u) ==
  \/ AgeBand[u] = "ok"              \* người ≥16 tự đồng ý
  \/ consent[u] = "active"          \* trẻ <16 phải có đồng ý giám hộ active
```

### Hành động
```tla
GrantConsent(u) ==
  /\ AgeBand[u] = "under_16"
  /\ consent[u] \in {"none", "revoked"}
  /\ consent' = [consent EXCEPT ![u] = "active"]
  /\ UNCHANGED artifacts

RevokeConsent(u) ==
  /\ consent[u] = "active"
  /\ consent' = [consent EXCEPT ![u] = "revoked"]
  /\ UNCHANGED artifacts

\* Sinh dữ liệu hướng nghiệp (trắc nghiệm/gợi ý) — CHỈ enabled khi CanProcess
ProcessCareerData(u) ==
  /\ CanProcess(u)
  /\ artifacts' = artifacts \cup
       {[owner |-> u,
         consentAtCreation |-> IF AgeBand[u] = "under_16" THEN "active" ELSE "na"]}
  /\ UNCHANGED consent
```

### Thuộc tính kiểm chứng
```tla
(* CP-1: KHÔNG tồn tại artifact nào của trẻ <16 được tạo khi consent không active *)
ConsentInvariant ==
  \A a \in artifacts :
    (AgeBand[a.owner] = "under_16") => a.consentAtCreation = "active"

(* CP-2: Sau thu hồi, không xử lý mới cho tới khi active trở lại —
   suy ra từ guard CanProcess; TLC kiểm chứng không artifact nào sinh khi revoked *)
NoProcessingWhileRevoked ==
  [][ \A u \in Users :
        consent[u] = "revoked" => (ProcessCareerData(u) => FALSE) ]_<<consent, artifacts>>
```
**TLC chứng minh:** mọi interleaving của Grant/Revoke/Process đều giữ `ConsentInvariant`. Đây là bất biến pháp lý cốt lõi (Luật 91/2025 + NĐ 147/2024).

---

## Module 2: SensitiveDataAccess (CP-3)

### Mục đích
Chứng minh **mọi** lần đọc `AssessmentResult` (RIASEC/VIPS/MBTI, `is_sensitive=true`) đều sinh **đúng một** bản ghi `AuditLog` với `is_sensitive_access=true` — không có đường đọc nào bỏ qua audit.

### Biến & hành động
```tla
VARIABLES
  sensitiveReads,     \* Nat — số lần đọc kết quả nhạy cảm
  sensitiveAudits     \* Nat — số audit log nhạy cảm đã ghi

ReadSensitiveResult(reader, rid) ==
  \* Đọc và ghi audit NGUYÊN TỬ trong cùng giao dịch
  /\ sensitiveReads'  = sensitiveReads + 1
  /\ sensitiveAudits' = sensitiveAudits + 1

\* Hành động "xấu" PHẢI không bao giờ xảy ra (đọc mà không audit) —
\* mô hình hóa để TLC chứng minh tính bất khả đạt
BadReadWithoutAudit ==
  /\ sensitiveReads' = sensitiveReads + 1
  /\ UNCHANGED sensitiveAudits
```

### Thuộc tính
```tla
(* CP-3: số đọc nhạy cảm luôn bằng số audit nhạy cảm *)
AuditCompleteness == sensitiveReads = sensitiveAudits
```
**TLC chứng minh:** với `Next == ReadSensitiveResult(...)` (loại bỏ `BadReadWithoutAudit` khỏi spec hiện thực), `AuditCompleteness` là bất biến. `BadReadWithoutAudit` được giữ trong tài liệu để chứng minh nếu lọt vào code sẽ phá invariant ngay.

---

## Module 3: AuthorizationModel (CP-4)

### Mục đích
Không người dùng nào đọc/sửa/xóa dữ liệu của người khác, **trừ** quan hệ được cấp quyền tường minh: `guardian ↔ child`, `counselor ↔ student` (trong cùng `school_id`).

### Quan hệ & hành động
```tla
CONSTANTS
  GuardianOf,   \* [child -> guardian]
  CounselorOf,  \* tập cặp <<counselor, student>> trong cùng trường

CanAccess(actor, owner) ==
  \/ actor = owner
  \/ (owner \in DOMAIN GuardianOf /\ GuardianOf[owner] = actor)
  \/ <<actor, owner>> \in CounselorOf

\* Hành động phải bất khả đạt nếu vi phạm
UnauthorizedAccess(actor, owner) ==
  /\ ~CanAccess(actor, owner)
  /\ UNCHANGED vars     \* nếu enabled => vi phạm
```

### Thuộc tính
```tla
(* CP-4: không có truy cập nào tới owner mà actor không có quyền *)
OwnershipInvariant ==
  \A actor, owner \in Users :
    AccessGranted(actor, owner) => CanAccess(actor, owner)
```
**TLC chứng minh:** `UnauthorizedAccess` không bao giờ enabled trên không gian trạng thái bị chặn.

---

## Module 4: RecommendationGovernance (CP-5, CP-6)

### Mục đích
(a) **Không** hành động phân luồng/chọn nghề nào được hệ thống tự thực hiện — gợi ý chỉ có hiệu lực sau khi **con người** xác nhận (Luật 134/2025 Đ.4 + không ép buộc TT 16/2026). (b) **Mọi** gợi ý đều có `rationale` không rỗng.

### Biến & hành động
```tla
VARIABLES
  recs        \* [rid -> [rationale |-> STRING, status, confirmedBy]]
              \* status \in {"proposed","accepted","rejected","deferred"}
              \* confirmedBy \in Users \cup {"NONE"}

CreateRecommendation(rid, rationaleText) ==
  /\ rid \notin DOMAIN recs
  /\ rationaleText # ""                       \* GUARD CP-6: bắt buộc có lý do
  /\ recs' = recs @@ (rid :> [rationale |-> rationaleText,
                              status |-> "proposed",
                              confirmedBy |-> "NONE"])

\* Chỉ CON NGƯỜI mới chuyển trạng thái sang có hiệu lực
ConfirmByHuman(rid, human, decision) ==
  /\ rid \in DOMAIN recs
  /\ recs[rid].status = "proposed"
  /\ human \in Users                          \* tác nhân người, không phải hệ thống
  /\ decision \in {"accepted","rejected","deferred"}
  /\ recs' = [recs EXCEPT ![rid].status = decision,
                          ![rid].confirmedBy = human]

\* Hành động phân luồng chỉ enabled khi đã có xác nhận người = "accepted"
ApplyPathway(rid) ==
  /\ recs[rid].status = "accepted"
  /\ recs[rid].confirmedBy # "NONE"
  /\ UNCHANGED recs
```

### Thuộc tính
```tla
(* CP-6: không gợi ý nào thiếu lý do *)
RecommendationRationale ==
  \A rid \in DOMAIN recs : recs[rid].rationale # ""

(* CP-5: gợi ý chỉ có hiệu lực (accepted/rejected/deferred) khi do con người xác nhận *)
HumanInTheLoop ==
  \A rid \in DOMAIN recs :
    recs[rid].status \in {"accepted","rejected","deferred"}
      => recs[rid].confirmedBy \in Users
```
**TLC chứng minh:** không tồn tại đường nào để `status` rời `"proposed"` mà `confirmedBy = "NONE"`; mọi `recs[rid].rationale # ""`.

---

## Module 5: AuthTokenLifecycle (CP-7)

### Mục đích
Xoay token nguyên tử (không có cửa sổ tồn tại hai token active cho một phiên) và token đã thu hồi không tái sử dụng được.

### Biến & bất biến
```tla
VARIABLES
  tokens,     \* [token_id -> [user_id, status, expires_at]]
  time        \* đồng hồ tăng đơn điệu
\* status \in {"active","revoked_logout","revoked_rotation","expired"}

AtMostOneActiveToken ==
  \A u \in Users :
    Cardinality({id \in DOMAIN tokens :
      tokens[id].user_id = u /\ tokens[id].status = "active"}) <= 1
```

### Xoay vòng nguyên tử & chống tái sử dụng
```tla
RotateToken(old_id, user) ==
  /\ old_id \in DOMAIN tokens
  /\ tokens[old_id].user_id = user
  /\ tokens[old_id].status = "active"
  /\ LET new_id == CHOOSE id \in Token_IDs : id \notin DOMAIN tokens IN
       tokens' = [tokens EXCEPT ![old_id].status = "revoked_rotation"]
                 @@ (new_id :> [user_id |-> user, status |-> "active",
                                expires_at |-> time + TOKEN_TTL])
  /\ UNCHANGED time

UseToken(token_id, user) ==
  /\ token_id \in DOMAIN tokens
  /\ tokens[token_id].status = "active"      \* FAIL nếu đã thu hồi
  /\ tokens[token_id].expires_at > time      \* FAIL nếu hết hạn
  /\ tokens[token_id].user_id = user
  /\ UNCHANGED <<tokens, time>>

(* CP-7: token đã thu hồi do xoay vòng không thể dùng *)
RevokedTokenReuse ==
  \A id \in DOMAIN tokens :
    tokens[id].status = "revoked_rotation" =>
      ~ENABLED UseToken(id, tokens[id].user_id)
```
**TLC chứng minh:** sau `RotateToken`, `AtMostOneActiveToken` vẫn đúng (không có trạng thái cả old & new cùng `active`); `RevokedTokenReuse` đúng.

---

## Module 6: CompetencyProgress (CP-8)

### Mục đích
Tiến bộ của một `(user, competency)` trên trục độ sâu chỉ tiến **K → A → R**, không lùi trong cùng chu kỳ đánh giá hợp lệ; lịch sử được giữ (append-only, không ghi đè).

### Biến & thứ tự độ sâu
```tla
CONSTANTS Learners, Competencies
DepthRank == [K |-> 0, A |-> 1, R |-> 2]

VARIABLES
  depth,        \* [<<learner, comp>> -> {"none","K","A","R"}]
  history       \* tập bản ghi append-only [learner, comp, depth, t]

AdvanceDepth(l, c, newDepth) ==
  /\ DepthRank[newDepth] > DepthRank[depth[<<l,c>>]]   \* chỉ tiến lên
  /\ depth' = [depth EXCEPT ![<<l,c>>] = newDepth]
  /\ history' = history \cup {[learner|->l, comp|->c, depth|->newDepth]}
```

### Thuộc tính
```tla
(* CP-8: độ sâu hiện tại không bao giờ giảm *)
ProgressMonotonicity ==
  [][ \A l \in Learners, c \in Competencies :
        DepthRank[depth'[<<l,c>>]] >= DepthRank[depth[<<l,c>>]] ]_depth

(* Lịch sử append-only: chỉ thêm, không xóa/sửa *)
HistoryAppendOnly ==
  [][ history \subseteq history' ]_history
```

---

## Tham số TLC Model Check

```tla
CONSTANTS
  Users     = {"c1", "c2", "a1"}      \* c1,c2 trẻ <16; a1 ≥16
  AgeBand   = (c1 :> "under_16") @@ (c2 :> "under_16") @@ (a1 :> "ok")
  Token_IDs = {"t1","t2","t3","t4","t5"}
  TOKEN_TTL = 5
  Learners  = {"c1","a1"}
  Competencies = {"NL1","NL10"}        \* mẫu đại diện 12 năng lực

INVARIANTS
  TypeInvariant
  ConsentInvariant            \* CP-1
  AuditCompleteness           \* CP-3
  OwnershipInvariant          \* CP-4
  RecommendationRationale     \* CP-6
  HumanInTheLoop              \* CP-5
  AtMostOneActiveToken        \* CP-7

PROPERTIES
  NoProcessingWhileRevoked    \* CP-2
  RevokedTokenReuse           \* CP-7
  ProgressMonotonicity        \* CP-8
  HistoryAppendOnly           \* CP-8
```

**Kết quả TLC kỳ vọng:**
- Không gian trạng thái: ~20.000–80.000 trạng thái phân biệt (mô hình bị chặn)
- Không vi phạm bất biến nào
- Mọi thuộc tính thời gian thỏa mãn
- Thời gian: < 90 giây trên máy dev

> ⚠️ **Kỷ luật `/formal-verify`:** "TLC pass với invariant yếu = THẤT BẠI". Mỗi invariant phải kèm **sabotage-check**: cố tình phá (vd cho `ProcessCareerData` bỏ guard `CanProcess`, hoặc cho `status` rời "proposed" không cần human) và xác nhận TLC **bắt được** vi phạm. Không có sabotage-check ⇒ invariant chưa được tin.

---

## Tích hợp CI

```yaml
# .github/workflows/tla.yml
- name: Run TLC Model Checker
  run: |
    for m in ConsentLifecycle SensitiveDataAccess AuthorizationModel \
             RecommendationGovernance AuthTokenLifecycle CompetencyProgress; do
      java -jar tla2tools.jar -config tla/$m.cfg tla/$m.tla
    done
    # Fail CI nếu bất kỳ invariant nào bị vi phạm
```

Cấu trúc thư mục đặc tả:
```
tla/
├── ConsentLifecycle.tla / .cfg            # CP-1, CP-2  (gate pháp lý)
├── SensitiveDataAccess.tla / .cfg         # CP-3
├── AuthorizationModel.tla / .cfg          # CP-4
├── RecommendationGovernance.tla / .cfg    # CP-5, CP-6
├── AuthTokenLifecycle.tla / .cfg          # CP-7
└── CompetencyProgress.tla / .cfg          # CP-8
```

**Gate B (spec.md §7):** TLC pass là điều kiện merge khi thay đổi state machine của consent/recommendation/auth/progress.

---

## Giới hạn của mô hình (TLC không chứng minh được)

1. **Hiệu năng/độ trễ** — TLC chứng minh safety/liveness, không phải latency (xem NFR-01).
2. **Đúng đắn hiện thực** — TLA+ mô hình hóa spec; test xác minh code khớp spec.
3. **An toàn mật mã của JWT** — mô hình hóa như opaque; an toàn thật đến từ hiện thực.
4. **Chất lượng/độ thiên lệch của thuật toán gợi ý** — CP-5/CP-6 chứng minh *quy trình* (có người + có lý do), **không** chứng minh gợi ý *công bằng/đúng*. Tính công bằng được phủ bởi **bias testing** (NFR-12) — một gate riêng, không thay thế được bằng TLC.
5. **Nội dung "đồng ý" thực chất** — TLC chứng minh trạng thái consent, không chứng minh người giám hộ thực sự hiểu (phủ bởi UX + quy trình pháp lý).

Các khoảng trống này được phủ bởi: integration test, load test, **bias test**, security review, DPIA.
