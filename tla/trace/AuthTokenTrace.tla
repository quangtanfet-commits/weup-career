----------------------------- MODULE AuthTokenTrace -----------------------------
(* Gate B — replay NDJSON trace token của impl qua AuthTokenLifecycle (CP-7).   *)
(* Mỗi bước (Issue/Rotate/Logout) phải enabled trong spec; AtMostOneActiveToken *)
(* giữ suốt chuỗi rotation. Deadlock khi l > Len = tiêu thụ hết = conform.       *)
EXTENDS AuthTokenTraceBase, Json, IOUtils, Sequences, TLC

JsonFile ==
    IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "token_trace.ndjson"

TraceLog == ndJsonDeserialize(JsonFile)

VARIABLE l
traceVars == <<l>>

logline == TraceLog[l]
IsEvent(name) == l <= Len(TraceLog) /\ logline.event = name

TraceIssue ==
  /\ IsEvent("Issue")
  /\ Issue(logline.state.token, logline.user)
  /\ l' = l + 1

TraceRotate ==
  /\ IsEvent("Rotate")
  /\ Rotate(logline.state.old, logline.state.new)
  /\ l' = l + 1

TraceLogout ==
  /\ IsEvent("Logout")
  /\ Logout(logline.state.token)
  /\ l' = l + 1

TraceInit == Init /\ l = 1
TraceNext == TraceIssue \/ TraceRotate \/ TraceLogout
==================================================================================
