
# Temporal Claim-Evidence Graph Relations

Allowed claim relation assertions are equivalent_to, refines, supersedes, corrects, retracts, duplicate, and structural_conflict_candidate. Evidence roles are supports, opposes, context, and duplicate.

Relation edges remain assertions. They do not establish truth. A structural conflict candidate can mark incompatible object or polarity under overlapping time, jurisdiction, and version scope, but it must never emit one_claim_true=true or one_claim_false=true.

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.
