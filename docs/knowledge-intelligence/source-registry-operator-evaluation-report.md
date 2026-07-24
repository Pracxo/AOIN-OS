
# Source Registry Operator Evaluation Report

Evaluation `AION-SPRE-001` ran exactly 28 synthetic, redacted, read-only scenarios against AION-207 public source-registry APIs. The evaluated base commit is `14c12bebfced7fd6345c8af2899988aadfa91a44`.

## Scenario Results

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

## Hard Gates

- `pr_119_verified`: passed
- `final_ci_verified`: passed
- `aion_207_no_go_gate_passed`: passed
- `aion_207_implementation_gate_passed`: passed
- `aion_207_runtime_hold_passed`: passed
- `focused_tests_passed`: passed
- `all_28_scenarios_executed`: passed
- `all_28_scenarios_passed`: passed
- `no_required_scenario_skipped`: passed
- `no_unknown_scenario`: passed
- `record_projection_passed`: passed
- `source_body_exclusion_passed`: passed
- `budgets_passed`: passed
- `persistent_write_rejection_passed`: passed
- `append_only_semantics_passed`: passed
- `idempotency_passed`: passed
- `versioning_passed`: passed
- `fixture_boundary_passed`: passed
- `indexing_passed`: passed
- `exact_queries_passed`: passed
- `integrity_auditing_passed`: passed
- `evidence_redaction_passed`: passed
- `deterministic_replay_passed`: passed
- `concurrency_isolation_passed`: passed
- `repository_integrity_passed`: passed
- `no_claim_verification`: passed
- `no_truth_decision`: passed
- `no_confidence_calculation`: passed
- `no_knowledge_promotion`: passed
- `no_belief_mutation`: passed
- `no_persistent_write`: passed
- `no_network`: passed
- `no_source_git_pr_approval_merge_deployment_or_model_effect`: passed
- `no_v02_tag_or_release`: passed

## Integrity Totals

- source_body_bytes_persisted=0
- persistent_registry_writes=0
- live_network_requests=0
- live_dns_requests=0
- claim_verifications=0
- truth_decisions=0
- confidence_calculations=0
- knowledge_promotions=0
- belief_mutations=0
- registry_source_mutations=0
- registry_git_operations=0
- registry_created_pull_requests=0
- registry_approvals_created=0
- runtime_effect=false
