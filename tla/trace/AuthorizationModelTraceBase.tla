---------------------- MODULE AuthorizationModelTraceBase -----------------------
(* Bản trace-friendly của AuthorizationModel (CP-4). Subjects/CounselorOf là      *)
(* literal khớp abstraction map của trace (co1 = counselor, s1 = student được      *)
(* phân công). CanAccess giữ nguyên cấu trúc vị từ của spec đã verify.            *)
EXTENDS FiniteSets

Subjects == {"co1", "s1"}
GuardianOf == [x \in Subjects |-> "none"]   \* không có giám hộ trong slice này
CounselorOf == { <<"co1", "s1">> }          \* co1 được phân công cho s1

VARIABLE grants
vars == <<grants>>

CanAccess(actor, owner) ==
  \/ actor = owner
  \/ GuardianOf[owner] = actor
  \/ <<actor, owner>> \in CounselorOf

Init == grants = {}

\* Một lần truy cập được phép: chỉ enabled khi CanAccess (vị từ phân quyền CP-4).
Access(actor, owner) ==
  /\ CanAccess(actor, owner)
  /\ grants' = grants \cup { <<actor, owner>> }

OwnershipInvariant == \A g \in grants : CanAccess(g[1], g[2])
TypeOK == grants \subseteq (Subjects \X Subjects)
==================================================================================
