
# Temporal Claim-Evidence Graph Architecture

AION-208 authorizes AION-209 to implement an immutable temporal claim-evidence graph. The graph will represent explicit unverified claim assertions, source-registry evidence bindings, temporal scope, jurisdiction scope, version scope, relation edges, and structural contradiction candidates.

AION-209 is not implemented by AION-208. No claim graph source, graph database, API route, installed command, SDK runtime resource, scheduler, worker, or startup registration is added in this branch.

## Boundary

The graph represents assertions. It does not decide truth, calculate confidence, promote knowledge, mutate cognitive beliefs, parse source bodies, acquire network content, write persistent graph state, create runtime PRs, create approvals, merge, deploy, or train model weights.

## Authorization

`AION-208-KI-0003` is the sole active Knowledge Intelligence implementation authorization. It points to AION-209 and closes at AION-210.

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.
