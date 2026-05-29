------------------------- MODULE CompetencyProgressTrace ------------------------
(* Gate B — replay NDJSON trace `AdvanceDepth` của impl qua CompetencyProgress.  *)
(* Mỗi advance phải enabled (độ sâu mới > hiện tại). Trace tiêu thụ hết = CP-8   *)
(* monotonic được giữ trên impl. Một bước giảm → Advance không enabled → kẹt.    *)
EXTENDS CompetencyProgressTraceBase, Json, IOUtils, Sequences, TLC

JsonFile ==
    IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "competency_trace.ndjson"

TraceLog == ndJsonDeserialize(JsonFile)

VARIABLE l
traceVars == <<l>>

logline == TraceLog[l]
IsEvent(name) == l <= Len(TraceLog) /\ logline.event = name

TraceAdvance ==
  /\ IsEvent("AdvanceDepth")
  /\ Advance(logline.user, logline.state.competency, logline.state.depth)
  /\ l' = l + 1

TraceInit == Init /\ l = 1
TraceNext == TraceAdvance
==================================================================================
