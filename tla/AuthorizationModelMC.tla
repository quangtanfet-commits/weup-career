-------------------------- MODULE AuthorizationModelMC --------------------------
EXTENDS AuthorizationModel
\* s1=student, g1=guardian của s1, c1=counselor cùng trường s1,
\* s2=student trường khác, c2=counselor trường khác
MCSubjects == {"s1", "g1", "c1", "s2", "c2"}
MCGuardianOf == [x \in MCSubjects |-> IF x = "s1" THEN "g1" ELSE "none"]
MCCounselorOf == { <<"c1", "s1">> }   \* c1 phụ trách s1; c2 không phụ trách ai
==================================================================================
