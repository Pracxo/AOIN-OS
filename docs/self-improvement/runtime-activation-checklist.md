# Runtime Activation Checklist

AION-175 does not activate runtime self-improvement. This checklist defines the minimum evidence required before any future activation request can be reviewed.

## Required Evidence

- New authorization transaction with exact implementation scope.
- Exact human approval for commit, diff hash, benchmark fingerprint, rollback commit, deployment artifact, exposure budget, monitoring duration, and metric thresholds.
- Full security review and protected-core impact review.
- Holdout benchmark validation with unchanged holdout content.
- Test-integrity report proving no test weakening.
- Production observability plan.
- Rollback plan with verified rollback commit.
- Canary exposure budget with production exposure disabled until separately approved.
- Full CI success on the exact approved commit.

## Current Required Values

- `self_improvement_runtime_enabled=false`
- `self_rewrite_runtime_enabled=false`
- `automatic_merge_enabled=false`
- `production_canary_enabled=false`
- `production_deployment_enabled=false`
- `model_weight_training_enabled=false`
