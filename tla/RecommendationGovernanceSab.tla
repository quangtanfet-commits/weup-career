----------------------- MODULE RecommendationGovernanceSab ----------------------
(* SABOTAGE: thêm AutoApply tự chuyển proposed->accepted KHÔNG cần con người. *)
(* Kỳ vọng: vi phạm HumanInTheLoop (CP-5).                                    *)
RecIds == {"r1", "r2"}
Humans == {"student", "guardian"}
VARIABLE recs
vars == <<recs>>
RecStatus == {"absent", "proposed", "accepted", "rejected", "deferred"}
Init == recs = [r \in RecIds |-> [rationale |-> FALSE, status |-> "absent", confirmedBy |-> "none"]]
Create(r) ==
  /\ recs[r].status = "absent"
  /\ recs' = [recs EXCEPT ![r] = [rationale |-> TRUE, status |-> "proposed", confirmedBy |-> "none"]]
\* SABOTAGE: hệ thống tự áp dụng, confirmedBy vẫn "none"
AutoApply(r) ==
  /\ recs[r].status = "proposed"
  /\ recs' = [recs EXCEPT ![r].status = "accepted"]
Next == \/ \E r \in RecIds : Create(r)
        \/ \E r \in RecIds : AutoApply(r)
Spec == Init /\ [][Next]_vars
HumanInTheLoop ==
  \A r \in RecIds : recs[r].status \in {"accepted","rejected","deferred"}
                      => recs[r].confirmedBy \in Humans
==================================================================================
