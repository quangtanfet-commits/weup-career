--------------------- MODULE SensitiveDataAccessTraceBase -----------------------
(* Bản trace-friendly của SensitiveDataAccess (CP-3). Mỗi lần đọc dữ liệu nhạy   *)
(* cảm phải ghi ĐÚNG MỘT audit trong cùng giao dịch → reads tăng cùng audits.    *)
(* Bất biến AuditCompleteness (reads = audits) giữ ở mọi state.                   *)
EXTENDS Integers

MaxReads == 10

VARIABLES reads, audits
vars == <<reads, audits>>

Init == reads = 0 /\ audits = 0

\* Một lần đọc nhạy cảm: tăng reads VÀ audits cùng lúc (audit cùng giao dịch).
ReadSensitive ==
  /\ reads < MaxReads
  /\ reads' = reads + 1
  /\ audits' = audits + 1

AuditCompleteness == reads = audits
TypeOK == reads \in 0..MaxReads /\ audits \in 0..MaxReads
==================================================================================
