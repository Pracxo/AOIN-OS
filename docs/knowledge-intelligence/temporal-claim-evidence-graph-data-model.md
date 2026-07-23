
# Temporal Claim-Evidence Graph Data Model

`UnverifiedClaimAssertion` contains claim_id, claim_statement, normalized_claim_fingerprint, subject_id, predicate, object_value, object_type, polarity, modality, language, jurisdiction_scopes, version_scopes, valid_time_intervals, transaction_time, operator_supplied, unverified=true, verified=false, knowledge_promoted=false, belief_created=false, and runtime_effect=false.

`ClaimEvidenceBinding` contains binding_id, claim_id, source_registry_record_ids, snapshot_fingerprints, provenance_fingerprints, citation_ids, lineage_group_ids, evidence_role, created_at, verified_support=false, and runtime_effect=false.

`TemporalClaimEvidenceGraph` contains immutable claim nodes, evidence bindings, claim-relation edges, temporal indexes, jurisdiction indexes, version indexes, lineage indexes, integrity fingerprint, and runtime_effect=false.
