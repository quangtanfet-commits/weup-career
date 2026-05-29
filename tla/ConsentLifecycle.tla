---------------------------- MODULE ConsentLifecycle ----------------------------
(* CP-1, CP-2 — Không xử lý dữ liệu hướng nghiệp của trẻ <16 khi không có    *)
(* GuardianConsent active; thu hồi dừng xử lý mới. Spec: docs/spec.md §8.     *)
EXTENDS FiniteSets

CONSTANTS Users,            \* tập user id
          AgeBand           \* [Users -> {"under_16","ok"}]

VARIABLES consent,          \* [Users -> {"none","active","revoked"}]
          artifacts         \* tập [owner |-> Users, consentAtCreation |-> ConsentStatus]

vars == <<consent, artifacts>>

ConsentStatus == {"none", "active", "revoked"}
Artifact == [owner: Users, consentAtCreation: ConsentStatus]

TypeOK ==
  /\ consent \in [Users -> ConsentStatus]
  /\ artifacts \subseteq Artifact

Init ==
  /\ consent = [u \in Users |-> IF AgeBand[u] = "under_16" THEN "none" ELSE "active"]
  /\ artifacts = {}

\* Điều kiện ĐƯỢC PHÉP xử lý dữ liệu hướng nghiệp
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

\* Sinh dữ liệu (trắc nghiệm/gợi ý). Ghi lại trạng thái consent TẠI THỜI ĐIỂM tạo.
ProcessCareerData(u) ==
  /\ CanProcess(u)
  /\ artifacts' = artifacts \cup {[owner |-> u, consentAtCreation |-> consent[u]]}
  /\ UNCHANGED consent

Next ==
  \/ \E u \in Users : GrantConsent(u)
  \/ \E u \in Users : RevokeConsent(u)
  \/ \E u \in Users : ProcessCareerData(u)

Spec == Init /\ [][Next]_vars

\* CP-1: không artifact nào của trẻ <16 được tạo khi consent không active
ConsentInvariant ==
  \A a \in artifacts : (AgeBand[a.owner] = "under_16") => (a.consentAtCreation = "active")

\* CP-2: không dữ liệu nào được xử lý trong trạng thái thu hồi
NoRevokedProcessing ==
  \A a \in artifacts : a.consentAtCreation # "revoked"
==================================================================================
