# 0188: Operator-Approved Local Append-Only Knowledge and Memory-Projection Persistence

Status: Accepted

## Context

AION-223-GLM-0002 authorized AION-224 to implement an isolated local persistence core after AION-222 proved dry-run promotion transaction planning and AION-223 evaluated the operator path. The implementation needs bounded durable local evidence without enabling production memory writes, belief mutation, network access, automatic promotion, runtime APIs, schedulers, installed CLI commands, connectors, model providers, or v0.2 release readiness.

## Decision

AION-224 implements a separate operator-invoked SQLite store with schema v1, application_id 223224, user_version 1, strict path policy, explicit initialization, dual transaction approval, append-only tables, update/delete rejection triggers, atomic BEGIN IMMEDIATE persistence, exact idempotent replay, changed-replay rejection, global and per-transaction SHA-256 hash chains, exact read-only queries, checkpoint, backup, restore-to-new-store, and redacted receipts/incidents.

The store persists approved bounded knowledge statements, identities, versions, approval bindings, candidate evidence receipts, isolated semantic/episodic/procedural projection records, belief-projection candidate records, transaction receipts, and integrity ledger events only. It does not subclass or wrap MemoryRepository and does not create ApprovalRequest, ApprovalDecision, BeliefClaim, production memory rows, network calls, background jobs, or runtime routes.

## Consequences

Local persistence is available only through explicit operator invocation and new dual approval per transaction. The stored records remain evidence-bound and do not establish absolute truth. AION-223-GLM-0002 remains active, unconsumed, unexpired, non-reusable, and pending AION-225 closeout. AION-226 remains unapproved.
