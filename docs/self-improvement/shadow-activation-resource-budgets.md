# Shadow Activation Resource Budgets

AION-180 records `AION-180-SI-0007` as the sole active implementation authorization for AION-181. It authorizes construction of a disabled controlled shadow activation control plane only. It does not authorize activation, runtime enablement, source mutation, Git mutation, approval creation, merge, promotion, canary, deployment, model training, a v0.2 tag, or a v0.2 release.

AION-SOE-001 remains successful advisory evidence and is not an approval. `AION-177-SI-0006` remains closed, expired, and non-reusable.


Resource limits are exact and fail closed. Quality gain cannot override any limit.

- `maximum_activation_window_seconds=3600`
- `maximum_runs_per_activation=10`
- `maximum_observation_references_per_run=1000`
- `maximum_evaluation_records_per_run=1000`
- `maximum_failure_patterns_per_run=100`
- `maximum_hypotheses_per_run=50`
- `maximum_regression_test_proposals_per_run=25`
- `maximum_shadow_proposals_per_run=10`
- `maximum_concurrency=4`
- `maximum_wall_clock_seconds_per_run=1800`
- `maximum_benchmark_cost_units_per_run=50`
- `maximum_output_bytes_per_run=10485760`
- `maximum_total_output_bytes_per_activation=52428800`
- `maximum_operator_output_files_per_run=20`
- `maximum_retention_seconds=604800`
- `production_exposure_basis_points=0`
- `network_calls=0`
- `connector_calls=0`
- `provider_calls=0`
- `git_operations=0`
- `source_mutations=0`
- `real_pull_requests=0`
- `approvals_created=0`
- `merges=0`
- `runtime_promotions=0`
- `production_canaries=0`
- `deployments=0`
- `model_training_runs=0`

## AION-181 Disabled Shadow Activation Control Plane

AION-181 implements the AION-180-authorized disabled controlled shadow activation control plane.
It validates candidates, requests, externally supplied approval evidence, resource budgets, local redacted evidence bundles, monitoring snapshots, deactivation decisions, incident records, audit evidence, provenance evidence, operator review items, and simulation-only outcomes.

The control plane can validate and simulate future activation requests but cannot activate shadow mode. Shadow activation remains false, shadow-mode runtime remains false, actual activation remains unavailable, and every decision remains evidence only.

AION-180-SI-0007 remains active pending AION-182 closeout. AION-182 is the next formal closeout and operator-evaluation task. Actual activation requires another authorization after AION-182.
