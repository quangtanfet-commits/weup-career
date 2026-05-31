----------------------- MODULE SensitiveDataAccessTrace -------------------------
(* Gate B — replay NDJSON trace `CounselorReadStudent` (sensitiveAccess=TRUE) của *)
(* impl qua SensitiveDataAccess. Mỗi sự kiện đọc nhạy cảm phải là một ReadSensitive*)
(* được phép → reads/audits tăng song song. Trace tiêu thụ hết (l = Len+1) = CP-3 *)
(* AuditCompleteness giữ trên impl (mỗi đọc đúng 1 audit, không thừa không thiếu).*)
EXTENDS SensitiveDataAccessTraceBase, Json, IOUtils, Sequences, TLC

JsonFile ==
    IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "sensitive_read_trace.ndjson"

TraceLog == ndJsonDeserialize(JsonFile)

VARIABLE l
traceVars == <<l>>

logline == TraceLog[l]
IsEvent(name) == l <= Len(TraceLog) /\ logline.event = name

TraceRead ==
  /\ IsEvent("CounselorReadStudent")
  /\ logline.state.sensitiveAccess = TRUE
  /\ ReadSensitive
  /\ l' = l + 1

TraceInit == Init /\ l = 1
TraceNext == TraceRead
==================================================================================
