# Temporal Claim-Evidence Graph Resource Budgets

AION-208 authorizes the following AION-209 limits. Any violation fails closed.

- `maximum_claim_nodes_per_graph`=1000
- `maximum_evidence_bindings_per_graph`=5000
- `maximum_claim_relation_edges_per_graph`=5000
- `maximum_source_registry_references_per_claim`=50
- `maximum_citation_references_per_claim`=50
- `maximum_lineage_groups_per_claim`=20
- `maximum_jurisdictions_per_claim`=20
- `maximum_versions_per_claim`=20
- `maximum_temporal_intervals_per_claim`=8
- `maximum_relation_edges_per_claim`=100
- `maximum_query_results`=1000
- `maximum_fixture_records`=2000
- `maximum_fixture_bytes`=2097152
- `maximum_concurrent_readers`=4
- `maximum_concurrent_projections`=4
- `maximum_graph_write_batch`=0
- `maximum_source_body_bytes`=0
- `maximum_automatic_claim_extractions`=0
- `maximum_claim_verifications`=0
- `maximum_truth_decisions`=0
- `maximum_confidence_calculations`=0
- `maximum_knowledge_promotions`=0
- `maximum_belief_mutations`=0
- `maximum_network_calls`=0
- `maximum_search_provider_calls`=0
- `maximum_connector_calls`=0
- `maximum_model_provider_calls`=0
- `maximum_source_mutations`=0
- `maximum_git_operations`=0
- `maximum_runtime_created_pull_requests`=0
- `maximum_approvals_created`=0
- `maximum_deployments`=0
- `maximum_model_weight_changes`=0

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.
## AION-209 Exact Resource Limits

- `maximum_claim_nodes_per_graph=1000`
- `maximum_evidence_bindings_per_graph=5000`
- `maximum_claim_relation_edges_per_graph=5000`
- `maximum_source_registry_references_per_claim=50`
- `maximum_citation_references_per_claim=50`
- `maximum_lineage_groups_per_claim=20`
- `maximum_jurisdictions_per_claim=20`
- `maximum_versions_per_claim=20`
- `maximum_temporal_intervals_per_claim=8`
- `maximum_relation_edges_per_claim=100`
- `maximum_query_results=1000`
- `maximum_fixture_records=2000`
- `maximum_fixture_bytes=2097152`
- `maximum_concurrent_readers=4`
- `maximum_concurrent_projections=4`
- `maximum_graph_write_batch=0`
- `maximum_source_body_bytes=0`
- `maximum_automatic_claim_extractions=0`
- `maximum_claim_verifications=0`
- `maximum_truth_decisions=0`
- `maximum_confidence_calculations=0`
- `maximum_knowledge_promotions=0`
- `maximum_belief_mutations=0`
- `maximum_network_calls=0`
- `maximum_search_provider_calls=0`
- `maximum_connector_calls=0`
- `maximum_model_provider_calls=0`
- `maximum_source_mutations=0`
- `maximum_git_operations=0`
- `maximum_runtime_created_pull_requests=0`
- `maximum_approvals_created=0`
- `maximum_deployments=0`
- `maximum_model_weight_changes=0`

## AION-210 Claim Graph Evaluation and Epistemic Authorization

AION-210 completed read-only operator evaluation `AION-TCGE-001` for AION-209. The decision is `TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_PASS_RECOMMEND_EPISTEMIC_TRUTH_ENGINE_AUTHORIZATION`.

Current stage: temporal claim-evidence graph implemented, evaluated, in-memory, append-only, unverified, and persistent-write-disabled. Deterministic epistemic assessment is authorized for AION-211 and not implemented.

Required flags: `temporal_claim_evidence_graph_implemented=true`, `claim_graph_operator_evaluation_passed=true`, `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `epistemic_truth_engine_authorized=true`, `epistemic_truth_engine_implemented=false`, `absolute_truth_oracle_enabled=false`, `knowledge_promotion_enabled=false`, `belief_mutation_enabled=false`, `network_access_enabled=false`, `active_knowledge_implementation_authorization=AION-210-KI-0004`, `active_knowledge_implementation_task=AION-211`, `formal_closeout_task=AION-212`.

AION-209 represents unverified claims. AION-210 evaluated the graph. AION-211 will assess evidence rather than claim metaphysical certainty. Source independence and freshness will be explicit; unresolved contradiction will be preserved; knowledge promotion and belief mutation remain unavailable.
