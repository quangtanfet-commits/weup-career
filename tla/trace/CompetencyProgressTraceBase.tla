----------------------- MODULE CompetencyProgressTraceBase ----------------------
(* Bản trace-friendly của CompetencyProgress (Learners/Comps là string).        *)
(* Advance chỉ enabled khi độ sâu mới > hiện tại → mọi transition trong trace    *)
(* phải tăng ngặt (CP-8 monotonic). Depth rank: 1=K, 2=A, 3=R.                   *)
EXTENDS Integers

Learners == {"l1"}
Comps == {"c1", "c2"}
Pairs == Learners \X Comps

VARIABLE depth
vars == <<depth>>

Init == depth = [p \in Pairs |-> 0]

Advance(l, c, nd) ==
  /\ nd \in 1..3
  /\ nd > depth[<<l, c>>]
  /\ depth' = [depth EXCEPT ![<<l, c>>] = nd]

TypeOK == depth \in [Pairs -> 0..3]
==================================================================================
