----------------------------- MODULE ConsentTrace -------------------------------
(* Gate B — replay NDJSON trace của impl (consent/auth) qua ConsentLifecycle.   *)
(* Mỗi bước impl phải là một transition ĐƯỢC PHÉP của spec đã verify. TLC báo   *)
(* deadlock khi tiêu thụ hết trace (l > Len) = THÀNH CÔNG (impl conform).        *)
EXTENDS ConsentTraceBase, Integers, Json, IOUtils, Sequences, TLC

JsonFile ==
    IF "JSON" \in DOMAIN IOEnv THEN IOEnv.JSON ELSE "consent_trace.ndjson"

TraceLog == ndJsonDeserialize(JsonFile)

VARIABLE l
traceVars == <<l>>

logline == TraceLog[l]
IsEvent(name) == l <= Len(TraceLog) /\ logline.event = name

\* Mỗi action: sự kiện khớp + transition spec enabled + post-state khớp log.
TraceGrant ==
  /\ IsEvent("GrantConsent")
  /\ GrantConsent(logline.user)
  /\ consent'[logline.user] = logline.state.consent
  /\ l' = l + 1

TraceRevoke ==
  /\ IsEvent("RevokeConsent")
  /\ RevokeConsent(logline.user)
  /\ consent'[logline.user] = logline.state.consent
  /\ l' = l + 1

\* ProcessCareerData (submit trắc nghiệm): chỉ enabled khi CanProcess (consent
\* active cho <16). Sinh artifact với consentAtCreation = consent hiện tại, khớp
\* log. Khiến ConsentInvariant (CP-1) trở nên NON-vacuous (artifacts khác rỗng).
TraceProcess ==
  /\ IsEvent("ProcessCareerData")
  /\ ProcessCareerData(logline.user)
  /\ [owner |-> logline.user,
      consentAtCreation |-> logline.state.consentAtCreation] \in artifacts'
  /\ l' = l + 1

TraceInit == Init /\ l = 1
TraceNext == TraceGrant \/ TraceRevoke \/ TraceProcess
==================================================================================
