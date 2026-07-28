# Local Persistence Restore Implementation


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
