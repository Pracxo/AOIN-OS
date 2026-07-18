# 0156: Governed Self-Improvement Control Plane

Date: 2026-07-18

Status: Accepted

## Context

AION-164 completed persistent identity assertion replay protection and consumed `AION-163-PA-0007`. The next program requires a governed self-improvement control plane that can evaluate performance, identify repeat weaknesses, prepare evidence-bound proposals, and later drive approval-bound isolated patch workflows without allowing autonomous source approval or production self-rewrite.

## Decision

AION-165 creates `AION-165-SI-0001` for AION-166. The authorization covers governance contracts, lifecycle validation, protected-core boundaries, approval binding, change budgets, risk classification, rollback requirements, and benchmark evidence requirements.

The authorization keeps all autonomous runtime and production effects disabled:

- `self_improvement_runtime_enabled=false`
- `self_rewrite_runtime_enabled=false`
- `automatic_merge_enabled=false`
- `automatic_production_deployment_enabled=false`
- `human_approval_required=true`
- `exact_commit_approval_required=true`
- `exact_diff_hash_approval_required=true`
- `no_self_approval=true`
- `protected_core_dual_approval_required=true`
- `rollback_plan_required=true`
- `benchmark_evidence_required=true`
- `hidden_holdout_required=true`

## Consequences

AION-166 may implement the internal governance plane but may not create patches, mutate Git state, create pull requests, merge code, deploy, or train model weights. Protected-core edits require a separate proposal, dual approval, security review, full CI, holdout validation, and proof that benchmark controls are not weakened by the same change.
