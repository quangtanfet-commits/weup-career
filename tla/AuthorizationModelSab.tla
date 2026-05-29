------------------------- MODULE AuthorizationModelSab --------------------------
(* SABOTAGE: bỏ guard CanProcess khỏi Access. Kỳ vọng: vi phạm Ownership.     *)
EXTENDS FiniteSets
Subjects == {"s1", "g1", "c1", "s2", "c2"}
GuardianOf == [x \in Subjects |-> IF x = "s1" THEN "g1" ELSE "none"]
CounselorOf == { <<"c1", "s1">> }
CanAccess(actor, owner) ==
  \/ actor = owner \/ GuardianOf[owner] = actor \/ <<actor, owner>> \in CounselorOf
VARIABLE grants
vars == <<grants>>
Init == grants = {}
\* SABOTAGE: không kiểm tra CanAccess
Access(actor, owner) == grants' = grants \cup {<<actor, owner>>}
Next == \E a \in Subjects, o \in Subjects : Access(a, o)
Spec == Init /\ [][Next]_vars
OwnershipInvariant == \A g \in grants : CanAccess(g[1], g[2])
==================================================================================
