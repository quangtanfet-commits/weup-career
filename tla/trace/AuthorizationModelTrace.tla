------------------------ MODULE AuthorizationModelTrace -------------------------
(* Gate B — replay NDJSON trace `CounselorReadStudent` của impl qua               *)
(* AuthorizationModel. Mỗi truy cập counselor→student phải là một Access ĐƯỢC PHÉP *)
(* (CanAccess giữ). Trace tiêu thụ hết (l = Len+1) = CP-4 OwnershipInvariant giữ  *)
(* trên impl: impl không bao giờ cấp quyền đọc vượt quan hệ phân công.            *)
EXTENDS AuthorizationModelTraceBase, Integers, Json, IOUtils, Sequences, TLC

JsonFile ==
    IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "sensitive_read_trace.ndjson"

TraceLog == ndJsonDeserialize(JsonFile)

VARIABLE l
traceVars == <<l>>

logline == TraceLog[l]
IsEvent(name) == l <= Len(TraceLog) /\ logline.event = name

TraceAccess ==
  /\ IsEvent("CounselorReadStudent")
  /\ Access(logline.user, logline.state.student)
  /\ l' = l + 1

TraceInit == Init /\ l = 1
TraceNext == TraceAccess
==================================================================================
