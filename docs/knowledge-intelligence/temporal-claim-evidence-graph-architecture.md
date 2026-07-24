
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

## AION-210 Claim Graph Evaluation and Epistemic Authorization

AION-210 completed read-only operator evaluation `AION-TCGE-001` for AION-209. The decision is `TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_PASS_RECOMMEND_EPISTEMIC_TRUTH_ENGINE_AUTHORIZATION`.

Current stage: temporal claim-evidence graph implemented, evaluated, in-memory, append-only, unverified, and persistent-write-disabled. Deterministic epistemic assessment is authorized for AION-211 and not implemented.

Required flags: `temporal_claim_evidence_graph_implemented=true`, `claim_graph_operator_evaluation_passed=true`, `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `epistemic_truth_engine_authorized=true`, `epistemic_truth_engine_implemented=false`, `absolute_truth_oracle_enabled=false`, `knowledge_promotion_enabled=false`, `belief_mutation_enabled=false`, `network_access_enabled=false`, `active_knowledge_implementation_authorization=AION-210-KI-0004`, `active_knowledge_implementation_task=AION-211`, `formal_closeout_task=AION-212`.

AION-209 represents unverified claims. AION-210 evaluated the graph. AION-211 will assess evidence rather than claim metaphysical certainty. Source independence and freshness will be explicit; unresolved contradiction will be preserved; knowledge promotion and belief mutation remain unavailable.
