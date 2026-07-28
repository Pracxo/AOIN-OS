# Governed Learning and Memory Architecture Roadmap

`AION-GOVERNED-LEARNING-MEMORY-001` now has AION-222 implemented and AION-223 evaluated. AION-224 is the sole active implementation task under `AION-223-GLM-0002`.

| Task | State | Role |
| --- | --- | --- |
| `AION-221` | `closed_consumed_by_AION-222` | Governed Learning and Memory Integration Program charter and AION-222 authorization |
| `AION-222` | `implemented_pending_AION-223_closeout` | Deterministic approval-bound knowledge-promotion transaction and cognitive-memory projection-planning core |
| `AION-223` | `operator_evaluation_passed_local_persistence_authorized` | AION-222 operator evaluation and local append-only knowledge persistence authorization decision |
| `AION-224` | `authorized_not_implemented` | Operator-approved local append-only knowledge-version and cognitive-memory projection store implementation |
| `AION-225` | `planned_formal_closeout_not_authorized` | Persistent knowledge and cognitive-memory projection evaluation with engagement-learning application authorization decision |
| `AION-226` | `planned_not_authorized` | Operator-approved engagement-learning application plane |
| `AION-227` | `planned_not_authorized` | Governed continual-learning pilot authorization review |
| `AION-228` | `planned_not_authorized` | Controlled local continual-learning pilot |
| `AION-229` | `planned_not_authorized` | Final Governed Learning and Memory Integration Program evaluation and closeout |

AION-224 may implement only an isolated local append-only store after AION-223 authorization. AION-226 and later runtime learning work remain unapproved.


## AION-223 evaluation and local persistence authorization

AION-223 completed read-only operator evaluation `AION-GLMPE-001` with exact PASS decision `PROMOTION_TRANSACTION_OPERATOR_EVALUATION_PASS_RECOMMEND_LOCAL_APPEND_ONLY_KNOWLEDGE_PERSISTENCE_AUTHORIZATION`. `AION-221-GLM-0001` is closed, consumed by AION-222, expired, and non-reusable. `AION-223-GLM-0002` is the sole active Governed Learning and Memory implementation authorization for AION-224. AION-224 is authorized to implement an isolated, operator-invoked, local append-only knowledge-version and cognitive-memory projection store, but AION-223 creates no AION-224 source, no persistent store, no memory write, no belief mutation, no approval, no network call, no production exposure, no v0.2 tag, and no v0.2 release.

<!-- AION-224-IMPLEMENTATION-UPDATE:START -->

## AION-224 Implementation Update

AION-224 implements the AION-223-GLM-0002 authorized isolated local append-only knowledge-version and projection persistence core. The store is explicit and operator-invoked, uses standard-library SQLite only, and remains outside production memory, approval creation, belief creation, network access, background execution, schedulers, API routes, installed CLI entry points, model providers, connectors, deployments, v0.2 tags, and v0.2 releases.

Implemented controls:

- Schema v1 uses application_id 223224 and user_version 1.
- Store paths must be explicit absolute paths outside the repository, with synthetic-test paths under 0700 temporary directories and operator-local paths outside temporary directories.
- Initialization is explicit and creates a new 0600 database file.
- SQLite uses foreign keys, WAL, FULL synchronous mode, trusted_schema=OFF, recursive_triggers=OFF, temp_store=MEMORY, and extension loading disabled.
- Every AION table has BEFORE UPDATE and BEFORE DELETE append-only rejection triggers.
- Persistence requires a valid AION-222 dry-run-passed plan/result, ready_for_future_persistence_review=true, a one-hour local store authorization envelope, and two independent existing persistence approvals for knowledge_steward and memory_operator roles.
- Approval evidence stores only safe IDs and fingerprints; raw approval payloads, source bodies, source previews, prompts, hidden reasoning, credentials, private keys, confidential content, restricted content, and personal data are rejected.
- Transactions are atomic with BEGIN IMMEDIATE, deterministic row fingerprints, idempotent exact replay, changed-replay rejection, global and per-transaction hash chains, read-after-write verification, exact read-only queries, integrity audit, checkpoint, backup, and restore-to-new-store semantics.
- Local projection records are isolated evidence-bound records. Belief-projection records are candidates only and never create or mutate BeliefClaim records.
- The committed synthetic pilot records one transaction, one idempotent replay, one changed replay rejection, one update rejection, one delete rejection, backup integrity, restore integrity, and zero retained temporary database files.

State after AION-224:

- local_append_only_knowledge_store_implemented=true
- operator_invoked_local_persistence_available=true
- synthetic_local_persistence_pilot_completed=true
- general_persistent_knowledge_write_enabled=false
- background_persistent_knowledge_write_enabled=false
- production_persistent_knowledge_write_enabled=false
- existing_memory_repository_write_enabled=false
- actual_belief_creation_enabled=false
- actual_belief_mutation_enabled=false
- automatic_knowledge_promotion_enabled=false
- network_access_enabled=false
- runtime_enabled=false

AION-223-GLM-0002 remains active, unconsumed, unexpired, non-reusable, and pending AION-225 formal closeout. AION-226 remains unapproved.

<!-- AION-224-IMPLEMENTATION-UPDATE:END -->
