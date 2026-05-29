-------------------------- MODULE AuthTokenTraceBase ----------------------------
(* Bản trace-friendly của AuthTokenLifecycle (TokenIds/AppUsers là string).     *)
(* PHẠM VI: MỘT phiên (single-session) — rotation chain. Impl cho đa phiên      *)
(* (login nhiều lần = nhiều token active); AtMostOneActiveToken áp cho chuỗi    *)
(* rotation TRONG một phiên (xem GATE_B_CONFORMANCE.md, ranh giới trừu tượng).  *)
EXTENDS Integers, FiniteSets

TokenIds == {"t1", "t2", "t3"}
AppUsers == {"u1"}

VARIABLE tokens
vars == <<tokens>>

Status == {"unused", "active", "revoked_logout", "revoked_rotation"}
TokenRecord == [user: AppUsers \cup {"none"}, status: Status]

Init == tokens = [t \in TokenIds |-> [user |-> "none", status |-> "unused"]]

Issue(t, u) ==
  /\ tokens[t].status = "unused"
  /\ \A o \in TokenIds : ~(tokens[o].user = u /\ tokens[o].status = "active")
  /\ tokens' = [tokens EXCEPT ![t] = [user |-> u, status |-> "active"]]

Rotate(told, tnew) ==
  /\ told # tnew
  /\ tokens[told].status = "active"
  /\ tokens[tnew].status = "unused"
  /\ tokens' = [tokens EXCEPT ![told].status = "revoked_rotation",
                              ![tnew] = [user |-> tokens[told].user, status |-> "active"]]

Logout(t) ==
  /\ tokens[t].status = "active"
  /\ tokens' = [tokens EXCEPT ![t].status = "revoked_logout"]

AtMostOneActiveToken ==
  \A u \in AppUsers :
    Cardinality({t \in TokenIds : tokens[t].user = u /\ tokens[t].status = "active"}) <= 1
==================================================================================
