# Governed Learning and Memory Threat Model

## Primary Threats

- Treating a verified candidate as durable truth without approval and revalidation.
- Treating operator approval as factual proof.
- Losing source provenance, dissent, conflict, or rollback evidence.
- Writing cognitive memory before a separate persistence authorization exists.
- Creating automatic promotions from engagement signals.
- Letting runtime code create approvals, mutate source, mutate Git state, call tools, call providers, or activate production paths.

## Controls

AION-221 records explicit false runtime flags, zero-effect budgets, no AION-222 source files, inherited AION-220 closeout verification, and focused no-go scripts. AION-222 remains deterministic, dry-run, in-memory, approval-bound, and write-disabled.

## AION-222 threat model

AION-222 implements the AION-221-GLM-0001 authorized promotion-planning core as deterministic, approval-bound, dry-run, in-memory, and write-disabled.

The implemented surface binds verified-knowledge candidates to complete lineage, validates externally supplied approval evidence, enforces separation of duties, revalidates eligibility and integrity, derives knowledge identity, detects duplicate and conflict conditions, plans append-only versions, prepares semantic, episodic, procedural, and belief-candidate projection plans, validates rollback and compensation, records immutable in-memory journal entries, and emits redacted operator review evidence.

This artifact does not authorize persistence. Persistent knowledge writes, verified-candidate persistence, semantic/episodic/procedural/cognitive-memory writes, belief creation or mutation, approval creation, automatic promotion, network access, runtime registration, production exposure, v0.2 tagging, and v0.2 release creation remain disabled.
