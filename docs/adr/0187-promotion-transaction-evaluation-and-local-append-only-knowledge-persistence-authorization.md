# ADR 0187: Promotion Transaction Evaluation and Local Append-Only Knowledge Persistence Authorization

Status: Accepted
Task: AION-223
Evaluation: AION-GLMPE-001
Decision: `PROMOTION_TRANSACTION_OPERATOR_EVALUATION_PASS_RECOMMEND_LOCAL_APPEND_ONLY_KNOWLEDGE_PERSISTENCE_AUTHORIZATION`

## Context

AION-222 implemented a deterministic, approval-bound, dry-run, in-memory knowledge-promotion transaction and cognitive-memory projection-planning core under `AION-221-GLM-0001`. It did not persist knowledge, write cognitive memory, create beliefs, create approvals, call networks or tools, or enable production runtime.

## Decision

AION-223 records a passing read-only operator evaluation and closes `AION-221-GLM-0001` as consumed by AION-222. On exact PASS it creates `AION-223-GLM-0002` as the sole active Governed Learning and Memory implementation authorization for AION-224.

AION-224 may implement an isolated, operator-invoked, local append-only knowledge-version and cognitive-memory projection store with explicit dual transaction approval, transactional atomicity, deterministic versioning, hash-chain integrity, update and delete rejection, bounded redacted content, backup validation, and restore-to-new-store semantics.

## Consequences

AION-223 creates no AION-224 source, no database, no persistent state, no memory write, no belief mutation, no approval, no network call, no tool execution, no workflow change, no dependency, no migration, no API route, no installed CLI, no production activation, no v0.2 tag, and no v0.2 release.

Every future persistent transaction requires a new exact dual approval bound to the store, transaction result, knowledge content, projection, database path, and backup policy fingerprints. Belief projections remain candidate records and do not create or mutate actual beliefs.
