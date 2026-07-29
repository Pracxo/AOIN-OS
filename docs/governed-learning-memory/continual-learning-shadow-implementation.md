# Continual Learning Shadow Implementation

AION-228 implements the AION-227-GLM-0004 authorized controlled local continual-learning pilot. The pilot is operator-invoked, bounded to one three-cycle session, and remains pending final AION-229 evaluation and closeout.

## Implemented Surface

- Strict Pydantic contracts for authorization envelopes, session plans, cycle plans, stage commands, receipts, checkpoints, rollback plans, outcomes, exact queries, integrity reports, evidence bundles, and operator-review items.
- Closed per-cycle state machine with explicit one-stage commands and immutable receipt chains.
- Deterministic simulation mode using in-memory public DNS and HTTPS fixtures for CI.
- Operator-invoked live mode that delegates DNS, peer pinning, HTTPS, robots, content, response-size, and body-purge controls to existing Knowledge Intelligence public-research components.
- Approval-bound promotion planning, dual-approved temporary local persistence binding, read-only cross-cycle context, in-memory shadow adaptation, Cycle 3 abstention, rollback, cleanup, and redacted evidence.

## Runtime Boundary

- background_continual_learning_enabled=false
- scheduled_continual_learning_enabled=false
- automatic_cycle_continuation_enabled=false
- automatic_source_discovery_enabled=false
- automatic_candidate_approval_enabled=false
- automatic_knowledge_promotion_enabled=false
- automatic_persistence_enabled=false
- retained_pilot_store_enabled=false
- production_memory_write_enabled=false
- production_policy_mutation_enabled=false
- cognitive_memory_write_enabled=false
- actual_belief_creation_enabled=false
- actual_belief_mutation_enabled=false
- source_mutation_enabled=false
- git_mutation_enabled=false
- model_weight_training_enabled=false
- production_exposure=false

## Live Pilot Evidence

The committed live-pilot evidence is redacted and stored at `examples/governed-learning-memory/controlled-local-continual-learning-live-pilot-evidence.json`. It records safe domains, URL fingerprints, claim fingerprint, counts, cycle outcomes, receipt-chain heads, and cleanup counters only.

AION-227-GLM-0004 remains active, unconsumed, unexpired, and non-reusable. AION-229 is the formal final evaluation and closeout task.
