--------------------------- MODULE ConsentTraceBase -----------------------------
(* Bản trace-friendly của ConsentLifecycle (Users/AgeBand là string literal để  *)
(* khớp khóa JSON khi replay). Hành động giữ nguyên ngữ nghĩa CP-1/CP-2.        *)
EXTENDS FiniteSets

Users == {"c1", "a1"}                      \* c1 = trẻ <16, a1 = người >=16
AgeBand == [u \in Users |-> IF u = "a1" THEN "ok" ELSE "under_16"]

VARIABLES consent, artifacts
vars == <<consent, artifacts>>

ConsentStatus == {"none", "active", "revoked"}
Artifact == [owner: Users, consentAtCreation: ConsentStatus]

Init ==
  /\ consent = [u \in Users |-> IF AgeBand[u] = "under_16" THEN "none" ELSE "active"]
  /\ artifacts = {}

CanProcess(u) == (AgeBand[u] = "ok") \/ (consent[u] = "active")

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

ProcessCareerData(u) ==
  /\ CanProcess(u)
  /\ artifacts' = artifacts \cup {[owner |-> u, consentAtCreation |-> consent[u]]}
  /\ UNCHANGED consent

ConsentInvariant ==
  \A a \in artifacts : (AgeBand[a.owner] = "under_16") => (a.consentAtCreation = "active")

NoRevokedProcessing ==
  \A a \in artifacts : a.consentAtCreation # "revoked"
==================================================================================
