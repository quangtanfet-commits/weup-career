------------------------- MODULE SensitiveDataAccessSab -------------------------
(* SABOTAGE: đọc nhạy cảm KHÔNG ghi audit. Kỳ vọng: vi phạm AuditCompleteness *)
EXTENDS Naturals
MaxReads == 5
VARIABLES reads, audits
vars == <<reads, audits>>
Init == reads = 0 /\ audits = 0

\* SABOTAGE: chỉ tăng reads, bỏ audit
BadRead ==
  /\ reads < MaxReads
  /\ reads' = reads + 1
  /\ UNCHANGED audits

Next == BadRead
Spec == Init /\ [][Next]_vars
AuditCompleteness == reads = audits
==================================================================================
