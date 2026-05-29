-------------------------- MODULE RecommendationTraceBase -----------------------
(* Bản trace-friendly của RecommendationGovernance (RecIds/Humans là string      *)
(* literal để khớp khóa JSON khi replay). Giữ nguyên ngữ nghĩa CP-5/CP-6.        *)
EXTENDS FiniteSets

RecIds == {"r1"}                  \* một gợi ý trong luồng trace (abstraction)
Humans == {"u1"}                  \* người dùng/giám hộ/GV xác nhận

VARIABLE recs
vars == <<recs>>

RecStatus == {"absent", "proposed", "accepted", "rejected", "deferred"}
RecRecord == [rationale: BOOLEAN, status: RecStatus, confirmedBy: Humans \cup {"none"}]

Init == recs = [r \in RecIds |-> [rationale |-> FALSE, status |-> "absent", confirmedBy |-> "none"]]

\* Tạo gợi ý: BẮT BUỘC rationale = TRUE (CP-6); proposed; chưa ai xác nhận.
Create(r) ==
  /\ recs[r].status = "absent"
  /\ recs' = [recs EXCEPT ![r] = [rationale |-> TRUE, status |-> "proposed", confirmedBy |-> "none"]]

\* Chỉ CON NGƯỜI mới chuyển sang trạng thái có hiệu lực (CP-5).
Confirm(r, h, d) ==
  /\ recs[r].status = "proposed"
  /\ h \in Humans
  /\ d \in {"accepted", "rejected", "deferred"}
  /\ recs' = [recs EXCEPT ![r].status = d, ![r].confirmedBy = h]

\* CP-6: gợi ý đã tồn tại luôn có rationale.
RationaleAlways == \A r \in RecIds : recs[r].status # "absent" => recs[r].rationale = TRUE

\* CP-5: trạng thái có hiệu lực phải do con người xác nhận.
HumanInTheLoop ==
  \A r \in RecIds : recs[r].status \in {"accepted", "rejected", "deferred"}
                      => recs[r].confirmedBy \in Humans
==================================================================================
