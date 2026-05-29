--------------------------- MODULE ConsentLifecycleSab --------------------------
(* SABOTAGE: bỏ guard CanProcess khỏi ProcessCareerData.                       *)
(* Kỳ vọng: TLC PHẢI báo vi phạm ConsentInvariant / NoRevokedProcessing.       *)
EXTENDS FiniteSets

Users == {"c1", "c2", "a1"}
AgeBand == [u \in Users |-> IF u = "a1" THEN "ok" ELSE "under_16"]

VARIABLES consent, artifacts
vars == <<consent, artifacts>>
ConsentStatus == {"none", "active", "revoked"}
Artifact == [owner: Users, consentAtCreation: ConsentStatus]

Init ==
  /\ consent = [u \in Users |-> IF AgeBand[u] = "under_16" THEN "none" ELSE "active"]
  /\ artifacts = {}

GrantConsent(u) ==
  /\ AgeBand[u] = "under_16"
  /\ consent[u] \in {"none", "revoked"}
  /\ consent' = [consent EXCEPT ![u] = "active"]
  /\ UNCHANGED artifacts

RevokeConsent(u) ==
  /\ AgeBand[u] = "under_16"
  /\ consent[u] = "active"
  /\ consent' = [consent EXCEPT ![u] = "revoked"]
  /\ UNCHANGED artifacts

\* SABOTAGE: KHÔNG còn guard CanProcess
ProcessCareerData(u) ==
  /\ artifacts' = artifacts \cup {[owner |-> u, consentAtCreation |-> consent[u]]}
  /\ UNCHANGED consent

Next ==
  \/ \E u \in Users : GrantConsent(u)
  \/ \E u \in Users : RevokeConsent(u)
  \/ \E u \in Users : ProcessCareerData(u)

Spec == Init /\ [][Next]_vars

ConsentInvariant ==
  \A a \in artifacts : (AgeBand[a.owner] = "under_16") => (a.consentAtCreation = "active")
==================================================================================
