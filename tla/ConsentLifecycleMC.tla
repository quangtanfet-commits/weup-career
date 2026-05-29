--------------------------- MODULE ConsentLifecycleMC ---------------------------
EXTENDS ConsentLifecycle

\* Mô hình nhỏ nhất còn thú vị: 2 trẻ <16 + 1 người >=16
MCUsers == {"c1", "c2", "a1"}
MCAgeBand == [u \in MCUsers |-> IF u = "a1" THEN "ok" ELSE "under_16"]
==================================================================================
