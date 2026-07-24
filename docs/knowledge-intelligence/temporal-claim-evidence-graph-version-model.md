
# Temporal Claim-Evidence Graph Version Model

Version scope records document, software, policy, or artifact versions for an unverified claim assertion. Version mismatch may produce structural conflict candidates. Corrections, retractions, and supersession edges remain append-only relation assertions.

AION-209 must prevent supersession cycles, self-support, self-contradiction, and relation-edge tampering.

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.
