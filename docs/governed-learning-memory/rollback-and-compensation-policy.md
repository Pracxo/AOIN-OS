# Rollback and Compensation Policy

A promotion transaction plan must include idempotency checks, rollback steps, and compensation steps before any later persistence task can be considered. Rollback planning is mandatory even when AION-222 remains write-disabled.

AION-222 may validate rollback and compensation plans in memory. It may not execute rollback against persistent knowledge, memory, source, Git, or production runtime.

## AION-222 rollback and compensation

AION-222 implements the AION-221-GLM-0001 authorized promotion-planning core as deterministic, approval-bound, dry-run, in-memory, and write-disabled.

The implemented surface binds verified-knowledge candidates to complete lineage, validates externally supplied approval evidence, enforces separation of duties, revalidates eligibility and integrity, derives knowledge identity, detects duplicate and conflict conditions, plans append-only versions, prepares semantic, episodic, procedural, and belief-candidate projection plans, validates rollback and compensation, records immutable in-memory journal entries, and emits redacted operator review evidence.

This artifact does not authorize persistence. Persistent knowledge writes, verified-candidate persistence, semantic/episodic/procedural/cognitive-memory writes, belief creation or mutation, approval creation, automatic promotion, network access, runtime registration, production exposure, v0.2 tagging, and v0.2 release creation remain disabled.
