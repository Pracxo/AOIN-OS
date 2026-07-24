
# Source Registry Evaluation Scenarios

AION-208 executes exactly the following scenario IDs. Every scenario passed in `AION-SPRE-001`.

- `valid_evidence_projection`: passed
- `strict_record_envelope`: passed
- `source_body_and_preview_exclusion`: passed
- `record_count_budget`: passed
- `envelope_and_metadata_budget`: passed
- `persistent_write_fail_closed`: passed
- `pure_in_memory_append`: passed
- `idempotent_replay`: passed
- `changed_payload_same_id_rejected`: passed
- `sequence_and_chain_integrity`: passed
- `payload_and_record_fingerprints`: passed
- `valid_supersession`: passed
- `invalid_supersession`: passed
- `fixture_path_boundary`: passed
- `fixture_schema_and_chain`: passed
- `deterministic_index_build`: passed
- `exact_queries`: passed
- `retrieval_time_range_query`: passed
- `query_limits_and_truncation`: passed
- `unresolved_reference_integrity`: passed
- `lineage_and_independence_integrity`: passed
- `registry_evidence_redaction`: passed
- `operator_review_boundary`: passed
- `deterministic_replay`: passed
- `changed_input_changes_fingerprints`: passed
- `concurrency_isolation`: passed
- `performance_smoke`: passed
- `no_truth_knowledge_belief_runtime_or_repository_effect`: passed

The scenarios cover deterministic projection, strict envelopes, source-body exclusion, budgets, persistent-write rejection, append-only semantics, idempotency, sequence and fingerprint integrity, supersession, fixture boundaries, indexes, exact queries, reference integrity, redaction, deterministic replay, concurrency isolation, performance smoke, and zero truth/knowledge/belief/runtime effects.
