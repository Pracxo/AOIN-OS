# Shadow Activation Approval Binding

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.


Future approval validation must bind exact candidate, commit, tree, diff, implementation evidence, evaluation report, benchmark manifest, benchmark result, reference set, operator scope, output boundary, run budget, monitoring plan, deactivation plan, rollback commit, operator principal, approvers, security reviewers, activation window, maximum runs, adapters, reference fingerprints, environment, approval time, expiry, consumed state, and `reusable=false`.

Required fields:

- activation_request_id
- activation_candidate_id
- base_commit_sha
- candidate_commit_sha
- candidate_tree_sha
- diff_sha256
- implementation_evidence_fingerprint
- evaluation_report_fingerprint
- benchmark_manifest_fingerprint
- benchmark_result_fingerprint
- reference_set_fingerprint
- operator_scope_fingerprint
- output_boundary_fingerprint
- run_budget_fingerprint
- monitoring_plan_fingerprint
- deactivation_plan_fingerprint
- rollback_commit_sha
- requesting_operator_principal_id
- approver_principal_ids
- security_reviewer_principal_ids
- activation_window_start
- activation_window_end
- maximum_runs
- approved_adapter_types
- approved_reference_fingerprints
- approved_environment
- approved_at
- expires_at
- consumed
- reusable
