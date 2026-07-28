# Approval and Separation of Duties

Operator approval is authorization evidence for a bounded transaction plan. It is not proof of factual truth and cannot replace source provenance, claim-scope revalidation, dissent preservation, conflict checks, freshness checks, or rollback planning.

AION-222 must validate approval expiry, approval revocation, approval binding, and separation of duties. Runtime-created approvals remain prohibited.

## AION-222 approval evidence

AION-222 implements the AION-221-GLM-0001 authorized promotion-planning core as deterministic, approval-bound, dry-run, in-memory, and write-disabled.

The implemented surface binds verified-knowledge candidates to complete lineage, validates externally supplied approval evidence, enforces separation of duties, revalidates eligibility and integrity, derives knowledge identity, detects duplicate and conflict conditions, plans append-only versions, prepares semantic, episodic, procedural, and belief-candidate projection plans, validates rollback and compensation, records immutable in-memory journal entries, and emits redacted operator review evidence.

This artifact does not authorize persistence. Persistent knowledge writes, verified-candidate persistence, semantic/episodic/procedural/cognitive-memory writes, belief creation or mutation, approval creation, automatic promotion, network access, runtime registration, production exposure, v0.2 tagging, and v0.2 release creation remain disabled.
