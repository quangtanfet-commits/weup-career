--------------------------- MODULE AuthorizationModel ---------------------------
(* CP-4 — Không truy cập chéo trừ quan hệ được cấp quyền (guardian↔child,     *)
(* counselor↔student cùng trường). spec.md §8.                                *)
EXTENDS FiniteSets

CONSTANTS Subjects,        \* tập actor/owner (user id)
          GuardianOf,      \* [Subjects -> Subjects \cup {"none"}]
          CounselorOf      \* tập <<counselor, student>>

VARIABLE grants            \* tập <<actor, owner>> đã được cấp truy cập
vars == <<grants>>

CanAccess(actor, owner) ==
  \/ actor = owner
  \/ GuardianOf[owner] = actor
  \/ <<actor, owner>> \in CounselorOf

TypeOK == grants \subseteq (Subjects \X Subjects)

Init == grants = {}

\* Truy cập chỉ được ghi nhận khi CanAccess
Access(actor, owner) ==
  /\ CanAccess(actor, owner)
  /\ grants' = grants \cup {<<actor, owner>>}

Next == \E a \in Subjects, o \in Subjects : Access(a, o)

Spec == Init /\ [][Next]_vars

\* CP-4: mọi truy cập đã ghi nhận đều thỏa CanAccess
OwnershipInvariant == \A g \in grants : CanAccess(g[1], g[2])
==================================================================================
