------------------------- MODULE AuthTokenLifecycleSab --------------------------
(* SABOTAGE: Rotate KHÔNG revoke token cũ (mất tính nguyên tử).               *)
(* Kỳ vọng: vi phạm AtMostOneActiveToken (CP-7).                              *)
EXTENDS Integers, FiniteSets
TokenIds == {"t1", "t2", "t3"}
AppUsers == {"u1", "u2"}
VARIABLE tokens
vars == <<tokens>>
Init == tokens = [t \in TokenIds |-> [user |-> "none", status |-> "unused"]]
Issue(t, u) ==
  /\ tokens[t].status = "unused"
  /\ \A o \in TokenIds : ~(tokens[o].user = u /\ tokens[o].status = "active")
  /\ tokens' = [tokens EXCEPT ![t] = [user |-> u, status |-> "active"]]
\* SABOTAGE: tạo token active mới NHƯNG để token cũ vẫn active
BadRotate(told, tnew) ==
  /\ told # tnew
  /\ tokens[told].status = "active"
  /\ tokens[tnew].status = "unused"
  /\ tokens' = [tokens EXCEPT ![tnew] = [user |-> tokens[told].user, status |-> "active"]]
Next == \/ \E t \in TokenIds, u \in AppUsers : Issue(t, u)
        \/ \E a, b \in TokenIds : BadRotate(a, b)
Spec == Init /\ [][Next]_vars
AtMostOneActiveToken ==
  \A u \in AppUsers :
    Cardinality({t \in TokenIds : tokens[t].user = u /\ tokens[t].status = "active"}) <= 1
==================================================================================
