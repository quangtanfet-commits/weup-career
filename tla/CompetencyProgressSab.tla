-------------------------- MODULE CompetencyProgressSab -------------------------
(* SABOTAGE: cho phép tụt mức (Decrease). Kỳ vọng: vi phạm Monotone (CP-8).   *)
EXTENDS Naturals
Learners == {"l1", "l2"}
Comps == {"NL1", "NL10"}
Pairs == Learners \X Comps
VARIABLE depth
vars == <<depth>>
Init == depth = [p \in Pairs |-> 0]
Advance(l, c, nd) == /\ nd \in 1..3 /\ nd > depth[<<l,c>>]
                     /\ depth' = [depth EXCEPT ![<<l,c>>] = nd]
\* SABOTAGE: cho phép giảm
Decrease(l, c, nd) == /\ nd \in 0..3 /\ nd < depth[<<l,c>>]
                      /\ depth' = [depth EXCEPT ![<<l,c>>] = nd]
Next == \/ \E l \in Learners, c \in Comps, nd \in 1..3 : Advance(l, c, nd)
        \/ \E l \in Learners, c \in Comps, nd \in 0..3 : Decrease(l, c, nd)
Spec == Init /\ [][Next]_vars
Monotone == [][ \A p \in Pairs : depth'[p] >= depth[p] ]_depth
==================================================================================
