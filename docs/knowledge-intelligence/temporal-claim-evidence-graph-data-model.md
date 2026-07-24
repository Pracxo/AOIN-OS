
# Temporal Claim-Evidence Graph Data Model

`UnverifiedClaimAssertion` contains claim_id, claim_statement, normalized_claim_fingerprint, subject_id, predicate, object_value, object_type, polarity, modality, language, jurisdiction_scopes, version_scopes, valid_time_intervals, transaction_time, operator_supplied, unverified=true, verified=false, knowledge_promoted=false, belief_created=false, and runtime_effect=false.

`ClaimEvidenceBinding` contains binding_id, claim_id, source_registry_record_ids, snapshot_fingerprints, provenance_fingerprints, citation_ids, lineage_group_ids, evidence_role, created_at, verified_support=false, and runtime_effect=false.

`TemporalClaimEvidenceGraph` contains immutable claim nodes, evidence bindings, claim-relation edges, temporal indexes, jurisdiction indexes, version indexes, lineage indexes, integrity fingerprint, and runtime_effect=false.

## AION-209 Immutable Temporal Claim-Evidence Graph

AION-209 implements the temporal claim-evidence graph core under `AION-208-KI-0003`. The graph represents explicit unverified claims, source-registry evidence bindings, valid time, transaction time, jurisdiction, version scope, relations, structural conflict candidates, immutable in-memory projection, deterministic indexes, bounded exact queries, fixture replay, integrity audit, and redacted operator-review evidence.

The current state is `implemented_append_only_in_memory_unverified_persistent_write_disabled`. `claim_graph_runtime_enabled=false`, `persistent_claim_graph_write_enabled=false`, `maximum_graph_write_batch=0`, `automatic_claim_extraction_enabled=false`, `claim_verification_enabled=false`, `truth_decision_enabled=false`, `epistemic_confidence_enabled=false`, `contradiction_resolution_enabled=false`, `knowledge_promotion_enabled=false`, and `belief_mutation_enabled=false`. AION-210 is the next formal closeout and evaluation task.
