--------------------------- MODULE RecommendationTrace --------------------------
(* Gate B — replay NDJSON trace của impl (reco engine) qua RecommendationGovernance.*)
(* Mỗi bước impl phải là transition ĐƯỢC PHÉP của spec đã verify. TLC báo deadlock *)
(* khi tiêu thụ hết trace (l > Len) = THÀNH CÔNG (impl conform CP-5/CP-6).          *)
EXTENDS RecommendationTraceBase, Integers, Json, IOUtils, Sequences, TLC

JsonFile ==
    IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "recommendation_trace.ndjson"

TraceLog == ndJsonDeserialize(JsonFile)

VARIABLE l
traceVars == <<l>>

logline == TraceLog[l]
IsEvent(name) == l <= Len(TraceLog) /\ logline.event = name

\* RecommendationCreated → Create: gợi ý mới, rationale phải khớp log (hasRationale).
TraceCreate ==
  /\ IsEvent("RecommendationCreated")
  /\ Create(logline.state.reco)
  /\ recs'[logline.state.reco].rationale = logline.state.hasRationale
  /\ l' = l + 1

\* RecommendationConfirmed → Confirm: do con người (confirmedBy) ghi quyết định.
TraceConfirm ==
  /\ IsEvent("RecommendationConfirmed")
  /\ Confirm(logline.state.reco, logline.state.confirmedBy, logline.state.confirmedDecision)
  /\ recs'[logline.state.reco].confirmedBy = logline.state.confirmedBy
  /\ l' = l + 1

TraceInit == Init /\ l = 1
TraceNext == TraceCreate \/ TraceConfirm
==================================================================================
