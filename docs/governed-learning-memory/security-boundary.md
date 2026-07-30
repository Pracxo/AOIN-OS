# Governed Learning and Memory Security Boundary

AION-221 is a charter and authorization task. The security boundary keeps `AION-222` unimplemented until a later source task consumes `AION-221-GLM-0001`.

## Denied Effects

- Runtime activation remains false.
- Persistent knowledge writes remain false.
- Cognitive-memory writes remain false.
- Belief creation and mutation remain false.
- Automatic candidate approval and automatic knowledge promotion remain false.
- Network, connector, model-provider, browser, shell, subprocess, and tool execution remain false.
- Source mutation, Git mutation, PR creation by runtime, deployment, and model-weight training remain false.
- v0.2 readiness, tags, and releases remain false or absent.

## Approval Boundary

Operator approval authorizes a bounded transaction plan. It does not make a claim true, suppress dissent, or bypass lineage, conflict, freshness, rollback, or persistence gates.

## AION-222 security boundary

AION-222 implements the AION-221-GLM-0001 authorized promotion-planning core as deterministic, approval-bound, dry-run, in-memory, and write-disabled.

The implemented surface binds verified-knowledge candidates to complete lineage, validates externally supplied approval evidence, enforces separation of duties, revalidates eligibility and integrity, derives knowledge identity, detects duplicate and conflict conditions, plans append-only versions, prepares semantic, episodic, procedural, and belief-candidate projection plans, validates rollback and compensation, records immutable in-memory journal entries, and emits redacted operator review evidence.

This artifact does not authorize persistence. Persistent knowledge writes, verified-candidate persistence, semantic/episodic/procedural/cognitive-memory writes, belief creation or mutation, approval creation, automatic promotion, network access, runtime registration, production exposure, v0.2 tagging, and v0.2 release creation remain disabled.

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

## AION-225 Evaluation And Authorization Update

AION-225 completed `AION-GLMPE-002` with exact PASS decision `LOCAL_APPEND_ONLY_PERSISTENCE_OPERATOR_EVALUATION_PASS_RECOMMEND_ENGAGEMENT_LEARNING_APPLICATION_AUTHORIZATION`. AION-223-GLM-0002 is closed as consumed by AION-224, expired and non-reusable. AION-225-GLM-0003 is the sole active Governed Learning and Memory implementation authorization for AION-226. Engagement learning remains non-factual, shadow-only, in-memory only, and unavailable until AION-226 implements it under the authorized boundary. Production memory writes, actual belief mutation, production policy mutation, persistent engagement overlays, network calls, model training, v0.2 tags and v0.2 releases remain disabled.
## AION-226 Engagement-Learning Shadow Application

AION-226 implements the AION-225-GLM-0003 authorized deterministic, operator-approved, non-factual engagement-learning shadow application plane. Overlays are in-memory only, apply only inside explicit bounded shadow sessions, expire or roll back before close, and create no persistent overlay, AION-224 store write, production policy mutation, factual or confidence effect, cognitive-memory write, belief mutation, model training, network call, runtime effect, v0.2 tag, or v0.2 release. AION-225-GLM-0003 remains active pending AION-227 closeout; AION-228 remains unapproved and AION-229 remains the final planned GLM closeout.

## AION-227 Engagement Evaluation And Continual-Learning Pilot Authorization

AION-GLMPE-003 passed all 28 deterministic, synthetic, read-only scenarios and closed AION-225-GLM-0003 as consumed by AION-226. AION-227-GLM-0004 is now the sole active GLM implementation authorization for AION-228, with AION-229 preserved as final GLM closeout.

AION-228 is authorized but unimplemented. Engagement remains non-factual; internet access remains explicit and allowlisted; local continuity remains temporary and isolated; every persistence and shadow adaptation remains approval-bound; background learning, scheduled learning, automatic approval, automatic promotion, code rewrite, production memory writes, belief mutation, production policy mutation and model training remain disabled.

## AION-228 Controlled Continual-Learning Pilot

AION-228 is implemented and completed pending AION-229 final evaluation and closeout. The pilot remains operator-invoked and local, executed one redacted three-cycle live session, purged source bodies, removed temporary persistence and overlay state, and keeps production memory, production policy, cognitive memory, belief mutation, source mutation, Git mutation, automatic approval, automatic promotion, background learning, scheduled learning, and model training disabled.

## AION-229 Final Program Evaluation

AION-229 final evaluation AION-GLMPE-004 passed all 28 deterministic hard-gated scenarios, validated the committed AION-228 live-pilot evidence, and closed AION-227-GLM-0004 as consumed by AION-228. The program is in primary closeout pending final Git evidence reconciliation. No active GLM implementation authorization, successor task, repeated-live-pilot authorization, or production runtime authorization remains.
