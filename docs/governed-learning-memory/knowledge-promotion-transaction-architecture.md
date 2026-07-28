# Knowledge Promotion Transaction Architecture

The planned transaction starts from an explicit verified-knowledge candidate and binds lineage, approval evidence, provenance revalidation, claim scope, epistemic confidence, domain dissent, tool attestation, conflict checks, duplicate checks, identity derivation, version planning, rollback planning, and an integrity audit.

AION-221 authorizes transaction planning only. AION-222 may model the transaction as deterministic, approval-bound, dry-run, and in-memory. It may not apply a durable knowledge promotion or persist a version.

## AION-222 transaction architecture

AION-222 implements the AION-221-GLM-0001 authorized promotion-planning core as deterministic, approval-bound, dry-run, in-memory, and write-disabled.

The implemented surface binds verified-knowledge candidates to complete lineage, validates externally supplied approval evidence, enforces separation of duties, revalidates eligibility and integrity, derives knowledge identity, detects duplicate and conflict conditions, plans append-only versions, prepares semantic, episodic, procedural, and belief-candidate projection plans, validates rollback and compensation, records immutable in-memory journal entries, and emits redacted operator review evidence.

This artifact does not authorize persistence. Persistent knowledge writes, verified-candidate persistence, semantic/episodic/procedural/cognitive-memory writes, belief creation or mutation, approval creation, automatic promotion, network access, runtime registration, production exposure, v0.2 tagging, and v0.2 release creation remain disabled.
