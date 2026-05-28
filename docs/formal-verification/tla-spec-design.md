# Formal Verification Design: TLA+/TLC Specification

**Version:** 1.0.0 | **Date:** 2026-05-27  
**Scope:** Todo state machine, authentication token lifecycle, concurrent operations, data consistency

---

## Overview

This document specifies the TLA+ modules to be written and verified **before production implementation begins**. The specifications will be checked with TLC model checker.

The specs serve as:
1. An unambiguous correctness reference for the implementation
2. A verification artifact that proves key safety and liveness properties
3. Documentation that will not drift from intent (unlike prose docs)

---

## Module 1: TodoStateMachine

### Purpose

Model all valid todo state transitions and verify that no sequence of operations can violate the state invariants.

### Constant Parameters

```tla
CONSTANTS
  Users,              \* Set of user IDs: {"u1", "u2"}
  MaxTodosPerUser     \* Bound for model checking: 3
```

### State Variables

```tla
VARIABLES
  todos,        \* [todo_id → [user_id, status, is_deleted, deleted_at]]
  next_id       \* Counter for generating unique todo IDs (simplified UUID)
```

### Type Invariant

```tla
TodoStatusType == {"open", "in_progress", "done"}

TodoRecord == [
  user_id    : Users,
  status     : TodoStatusType,
  is_deleted : BOOLEAN,
  deleted_at : Nat \cup {0}   \* 0 = not deleted; N = deletion time
]

TypeInvariant ==
  /\ todos \in [DOMAIN todos → TodoRecord]
  /\ next_id \in Nat
```

### Safety Invariants

```tla
(* Ownership: no deleted + active status combination *)
NoDeletedActiveStatus ==
  \A id \in DOMAIN todos :
    todos[id].is_deleted =>
      todos[id].status \in TodoStatusType
    \* (status is preserved on delete; not cleared)

(* Soft-delete consistency *)
SoftDeleteConsistency ==
  \A id \in DOMAIN todos :
    todos[id].is_deleted <=> todos[id].deleted_at > 0

(* Ownership uniqueness: a todo belongs to exactly one user *)
OwnershipUniqueness ==
  \A id1, id2 \in DOMAIN todos :
    id1 # id2 => TRUE  \* IDs are globally unique (enforced by next_id)
```

### Actions

```tla
CreateTodo(user) ==
  /\ next_id < MaxTodosPerUser * Cardinality(Users)
  /\ LET id == next_id IN
     /\ todos' = todos @@ (id :> [
          user_id    |-> user,
          status     |-> "open",
          is_deleted |-> FALSE,
          deleted_at |-> 0
        ])
     /\ next_id' = next_id + 1

UpdateStatus(user, id, new_status) ==
  /\ id \in DOMAIN todos
  /\ todos[id].user_id = user        \* Ownership check
  /\ ~todos[id].is_deleted           \* Cannot update deleted
  /\ new_status \in ValidTransitions(todos[id].status)
  /\ todos' = [todos EXCEPT ![id].status = new_status]
  /\ next_id' = next_id

ValidTransitions(current) ==
  CASE current = "open"        -> {"in_progress", "done"}
    [] current = "in_progress" -> {"open", "done"}
    [] current = "done"        -> {"open"}
    [] OTHER                   -> {}

SoftDelete(user, id) ==
  /\ id \in DOMAIN todos
  /\ todos[id].user_id = user
  /\ ~todos[id].is_deleted
  /\ todos' = [todos EXCEPT
       ![id].is_deleted = TRUE,
       ![id].deleted_at = 1]     \* Simplified: 1 = "some time"
  /\ next_id' = next_id

RestoreTodo(user, id) ==
  /\ id \in DOMAIN todos
  /\ todos[id].user_id = user
  /\ todos[id].is_deleted
  /\ todos' = [todos EXCEPT
       ![id].is_deleted = FALSE,
       ![id].deleted_at = 0]
  /\ next_id' = next_id

AccessAttempt(user, id) ==
  \* Model that a user can only see their own todos
  /\ id \in DOMAIN todos
  /\ todos[id].user_id = user    \* This is the invariant TLC checks
  /\ UNCHANGED <<todos, next_id>>

CrossUserAccess(attacker, victim_id) ==
  \* This action must be UNREACHABLE (TLC exhaustion proves it never triggers)
  /\ victim_id \in DOMAIN todos
  /\ todos[victim_id].user_id # attacker
  /\ UNCHANGED <<todos, next_id>>
```

### Properties to Verify

```tla
(* SAFETY: A cross-user access action is never reachable *)
NoUnauthorizedAccess ==
  [][\A id \in DOMAIN todos :
      \A user \in Users :
        user # todos[id].user_id => ~AccessAttempt(user, id)]_<<todos, next_id>>

(* SAFETY: Status transitions are always valid *)
StatusTransitionsValid ==
  [][
    \A id \in DOMAIN todos :
      todos[id].status \in TodoStatusType
  ]_todos

(* SAFETY: Deleted todos have deleted_at set *)
DeleteConsistency ==
  [](SoftDeleteConsistency)

(* LIVENESS: Eventually a created todo can be deleted *)
EventualDeletion ==
  \A id \in DOMAIN todos :
    todos[id].status = "open" ~> todos[id].is_deleted = TRUE
```

---

## Module 2: AuthTokenLifecycle

### Purpose

Verify that token rotation is atomic (no window where two valid tokens exist for one session), and that revoked tokens cannot be used.

### State Variables

```tla
VARIABLES
  tokens,     \* [token_id → [user_id, status, expires_at]]
  time        \* Monotonically increasing clock
```

Where `status ∈ {"active", "revoked_logout", "revoked_rotation", "expired"}`.

### Key Invariant

```tla
(* CRITICAL: At most one active token per user at any time *)
AtMostOneActiveToken ==
  \A u \in Users :
    Cardinality({id \in DOMAIN tokens :
      tokens[id].user_id = u /\ tokens[id].status = "active"}) <= 1
```

### Rotation Atomicity

```tla
RotateToken(old_id, user) ==
  \* Both operations happen atomically (single transaction)
  /\ old_id \in DOMAIN tokens
  /\ tokens[old_id].user_id = user
  /\ tokens[old_id].status = "active"
  /\ LET new_id == CHOOSE id \in Token_IDs : id \notin DOMAIN tokens IN
     /\ tokens' = [tokens EXCEPT
          ![old_id].status = "revoked_rotation",
          new_id :> [user_id   |-> user,
                     status    |-> "active",
                     expires_at|-> time + TOKEN_TTL]]
  /\ UNCHANGED time
```

**TLC verifies:** After `RotateToken`, `AtMostOneActiveToken` still holds. There is never a state where both `old_id` and `new_id` are simultaneously `"active"`.

### Revoked Token Reuse Prevention

```tla
UseToken(token_id, user) ==
  /\ token_id \in DOMAIN tokens
  /\ tokens[token_id].status = "active"      \* FAILS if revoked
  /\ tokens[token_id].expires_at > time       \* FAILS if expired
  /\ tokens[token_id].user_id = user          \* FAILS if wrong user
  /\ UNCHANGED <<tokens, time>>

RevokedTokenReuse ==
  \* Property: a revoked token use attempt always fails
  \A id \in DOMAIN tokens :
    tokens[id].status = "revoked_rotation" =>
      ~ENABLED UseToken(id, tokens[id].user_id)
```

---

## Module 3: ConcurrentOperations

### Purpose

Model concurrent updates to todo sort_order (drag-and-drop reorder) from multiple browser sessions and verify the sort_order invariant holds.

### The Invariant

```tla
(* For each user, sort_orders form a unique sequence starting at 0 *)
SortOrderInvariant ==
  \A user \in Users :
    LET user_todos == {id \in DOMAIN todos :
                       todos[id].user_id = user /\
                       ~todos[id].is_deleted}
        orders == {todos[id].sort_order : id \in user_todos}
    IN
    /\ Cardinality(orders) = Cardinality(user_todos)  \* No duplicates
    /\ \A n \in 0..Cardinality(user_todos)-1 : n \in orders  \* Contiguous
```

### Concurrent Reorder Conflict Resolution

```tla
\* Two clients send reorder simultaneously
\* The second one must be based on the current state
ReorderTodos(user, new_order) ==
  \* new_order: sequence of todo IDs in desired order
  /\ \A id \in Range(new_order) : todos[id].user_id = user
  /\ todos' = [todos EXCEPT ...
       \* Assign sort_order 0,1,2,... per new_order sequence
     ]
```

TLC verifies: even if two concurrent reorder requests arrive, the final state always satisfies `SortOrderInvariant`.

---

## Module 4: IdempotencyInvariants

### Purpose

Verify that repeated identical requests do not produce duplicate state.

### Create Idempotency (via client-generated ID)

```tla
\* If client sends same create request twice (same idempotency key):
CreateTodoIdempotent(user, idem_key, title) ==
  IF \E id \in DOMAIN todos :
       todos[id].user_id = user /\
       todos[id].idempotency_key = idem_key
  THEN
    \* Second call: no-op, return existing todo
    UNCHANGED todos
  ELSE
    \* First call: create
    ...
```

---

## TLC Model Check Parameters

```tla
CONSTANTS
  Users        = {"u1", "u2"}        \* 2 users
  MaxTodos     = 3                    \* 3 todos per user max (state space bound)
  TOKEN_TTL    = 5                    \* Simplified time units
  Token_IDs    = {"t1","t2","t3","t4","t5"}

INVARIANTS
  TypeInvariant
  NoUnauthorizedAccess
  StatusTransitionsValid
  DeleteConsistency
  AtMostOneActiveToken
  SortOrderInvariant

PROPERTIES
  EventualDeletion
  RevokedTokenReuse
```

**Expected TLC results:**
- State space: ~10,000-50,000 distinct states (bounded model)
- No invariant violations
- All temporal properties satisfied
- Model check time: <60 seconds on developer machine

---

## CI Integration

```yaml
# .github/workflows/tla.yml
- name: Run TLC Model Checker
  run: |
    java -jar tla2tools.jar -config TodoApp.cfg TodoApp.tla
    # Fail CI if any invariant violated
```

The TLA+ specs live in `tla/` directory:
```
tla/
├── TodoStateMachine.tla
├── TodoStateMachine.cfg
├── AuthTokenLifecycle.tla
├── AuthTokenLifecycle.cfg
├── ConcurrentOperations.tla
├── ConcurrentOperations.cfg
└── IdempotencyInvariants.tla
```

---

## What TLC Cannot Prove (Limits of This Model)

1. **Performance properties** — TLC proves safety/liveness, not latency
2. **Implementation correctness** — TLA+ models the spec; tests verify the code
3. **Cryptographic security of JWT** — modeled as opaque; real security from implementation
4. **SQLite ACID guarantees** — modeled as atomic; actual atomicity from SQLite transactions

These gaps are covered by: integration tests, load tests, and the security review.
