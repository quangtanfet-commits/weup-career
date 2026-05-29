--------------------------- MODULE AuthTokenLifecycle ---------------------------
(* CP-7 — Xoay token nguyên tử (không hai token cùng active); token thu hồi   *)
(* không tái dùng. spec.md §8.                                                *)
EXTENDS Integers, FiniteSets

CONSTANTS TokenIds, AppUsers
VARIABLE tokens   \* [TokenIds -> [user: AppUsers \cup {"none"}, status]]
vars == <<tokens>>

Status == {"unused", "active", "revoked_logout", "revoked_rotation"}
TokenRecord == [user: AppUsers \cup {"none"}, status: Status]

TypeOK == tokens \in [TokenIds -> TokenRecord]

Init == tokens = [t \in TokenIds |-> [user |-> "none", status |-> "unused"]]

Issue(t, u) ==
  /\ tokens[t].status = "unused"
  /\ \A o \in TokenIds : ~(tokens[o].user = u /\ tokens[o].status = "active")  \* chưa có active cho u
  /\ tokens' = [tokens EXCEPT ![t] = [user |-> u, status |-> "active"]]

\* Xoay vòng NGUYÊN TỬ: cùng lúc revoke cũ + active mới
Rotate(told, tnew) ==
  /\ told # tnew
  /\ tokens[told].status = "active"
  /\ tokens[tnew].status = "unused"
  /\ tokens' = [tokens EXCEPT ![told].status = "revoked_rotation",
                              ![tnew] = [user |-> tokens[told].user, status |-> "active"]]

Logout(t) ==
  /\ tokens[t].status = "active"
  /\ tokens' = [tokens EXCEPT ![t].status = "revoked_logout"]

Next ==
  \/ \E t \in TokenIds, u \in AppUsers : Issue(t, u)
  \/ \E told, tnew \in TokenIds : Rotate(told, tnew)
  \/ \E t \in TokenIds : Logout(t)

Spec == Init /\ [][Next]_vars

\* CP-7: tối đa một token active cho mỗi user tại mọi thời điểm
AtMostOneActiveToken ==
  \A u \in AppUsers :
    Cardinality({t \in TokenIds : tokens[t].user = u /\ tokens[t].status = "active"}) <= 1
==================================================================================
