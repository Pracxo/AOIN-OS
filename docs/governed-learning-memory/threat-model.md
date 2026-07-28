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

## AION-223 evaluation and local persistence authorization

AION-223 completed read-only operator evaluation `AION-GLMPE-001` with exact PASS decision `PROMOTION_TRANSACTION_OPERATOR_EVALUATION_PASS_RECOMMEND_LOCAL_APPEND_ONLY_KNOWLEDGE_PERSISTENCE_AUTHORIZATION`. `AION-221-GLM-0001` is closed, consumed by AION-222, expired, and non-reusable. `AION-223-GLM-0002` is the sole active Governed Learning and Memory implementation authorization for AION-224. AION-224 is authorized to implement an isolated, operator-invoked, local append-only knowledge-version and cognitive-memory projection store, but AION-223 creates no AION-224 source, no persistent store, no memory write, no belief mutation, no approval, no network call, no production exposure, no v0.2 tag, and no v0.2 release.
