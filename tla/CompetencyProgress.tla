--------------------------- MODULE CompetencyProgress ---------------------------
(* CP-8 — Tiến bộ độ sâu chỉ tiến K->A->R, không lùi. spec.md §8.             *)
EXTENDS Naturals

CONSTANTS Learners, Comps

Pairs == Learners \X Comps
\* Độ sâu: 0=none, 1=K, 2=A, 3=R
VARIABLE depth   \* [Pairs -> 0..3]
vars == <<depth>>

TypeOK == depth \in [Pairs -> 0..3]

Init == depth = [p \in Pairs |-> 0]

\* Chỉ nâng lên mức cao hơn (đạt chỉ báo sâu hơn)
Advance(l, c, nd) ==
  /\ nd \in 1..3
  /\ nd > depth[<<l, c>>]
  /\ depth' = [depth EXCEPT ![<<l, c>>] = nd]

Next == \E l \in Learners, c \in Comps, nd \in 1..3 : Advance(l, c, nd)

Spec == Init /\ [][Next]_vars

\* CP-8 (an toàn dạng action): độ sâu không bao giờ giảm
Monotone == [][ \A p \in Pairs : depth'[p] >= depth[p] ]_depth
==================================================================================
