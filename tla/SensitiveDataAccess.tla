--------------------------- MODULE SensitiveDataAccess --------------------------
(* CP-3 — Mọi lần đọc kết quả nhạy cảm sinh đúng 1 audit log. spec.md §8.     *)
EXTENDS Naturals

CONSTANTS MaxReads
VARIABLES reads, audits
vars == <<reads, audits>>

TypeOK == reads \in 0..MaxReads /\ audits \in 0..MaxReads

Init == reads = 0 /\ audits = 0

\* Đọc kết quả nhạy cảm: tăng read VÀ ghi audit trong cùng giao dịch
ReadSensitive ==
  /\ reads < MaxReads
  /\ reads'  = reads + 1
  /\ audits' = audits + 1

Next == ReadSensitive

Spec == Init /\ [][Next]_vars

\* CP-3: số đọc nhạy cảm luôn bằng số audit nhạy cảm
AuditCompleteness == reads = audits
==================================================================================
