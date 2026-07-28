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
