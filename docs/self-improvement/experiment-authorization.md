# Self-Improvement Experiment Authorization

Program: AION-SELF-IMPROVEMENT-001

Task: AION-169

## Purpose

AION-169 closes `AION-167-SI-0002` as consumed by AION-168 PR 79 and creates `AION-169-SI-0003` as the single active authorization for AION-170. The next implementation may add a bounded self-improvement proposal and experiment engine only.

The experiment engine may intake repeated failure patterns, form bounded improvement hypotheses, prepare regression-test proposals, define experiment plans, execute baseline and candidate experiment slots, classify risk, assemble evidence bundles, and move proposals to the approval-pending lifecycle state.

## Authorization

- `authorization_transaction_id=AION-169-SI-0003`
- `approval_record_id=AION-169-SI-0003`
- `parent_authorization_transaction_id=AION-167-SI-0002`
- `implementation_task=AION-170`
- `authorization_scope=self-improvement-proposal-and-experiment-engine`
- `authorization_active=true`
- `authorization_consumed=false`
- `authorization_expired=false`
- `authorization_reusable=false`

## Runtime State

- `self_improvement_runtime_enabled=false`
- `self_rewrite_runtime_enabled=false`
- `automatic_merge_enabled=false`
- `automatic_production_deployment_enabled=false`
- `source_rewriting_enabled=false`
- `source_mutation_enabled=false`
- `git_commits_enabled=false`
- `branch_creation_enabled=false`
- `pull_request_creation_enabled=false`
- `merge_enabled=false`
- `automatic_approval_enabled=false`
- `production_deployment_enabled=false`
- `deployment_enabled=false`
- `model_weight_training_enabled=false`
- `model_weight_changes_enabled=false`

## Approved Scope

- failure-pattern intake
- improvement hypotheses
- regression-test proposals
- experiment plans
- baseline/candidate experiment execution
- risk classification
- evidence bundles
- approval-pending lifecycle

## Prohibited Scope

AION-170 may not implement source mutation, source rewriting, Git commits, branch creation, Git mutation, pull request creation, merge, deployment, production deployment, automatic approval, model-weight changes, model-weight training, a v0.2 tag, a v0.2 release, or any modification to `aion-v0.1.0`.

The proposal and experiment engine may produce bounded plans and evidence records, but it may not promote code changes directly or convert any experiment result into a source change without a later, exact human approval transaction.
