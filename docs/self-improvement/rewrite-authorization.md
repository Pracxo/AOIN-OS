# Self-Improvement Rewrite Authorization

Program: AION-SELF-IMPROVEMENT-001

Task: AION-171

## Purpose

AION-171 closes `AION-169-SI-0003` as consumed by AION-170 PR 81 and creates `AION-171-SI-0004` as the single active authorization for AION-172. The next implementation may add an approval-bound isolated source-rewrite and PR-control plane only.

The authorized controller may prepare isolated worktrees, bounded patches, test-first evidence, diff hashes, approval-bound task branches, approval-bound commits, approval-bound pull requests, CI monitoring, merge controls, and rollback metadata. These capabilities remain inert unless an exact human approval binds the proposal, commit, diff hash, benchmark evidence, rollback commit, and deployment scope.

## Authorization

- `authorization_transaction_id=AION-171-SI-0004`
- `approval_record_id=AION-171-SI-0004`
- `parent_authorization_transaction_id=AION-169-SI-0003`
- `implementation_task=AION-172`
- `authorization_scope=approval-bound-isolated-source-rewrite-and-pr-control`
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

- ephemeral Git worktrees
- bounded file edits
- test-first patch workflow
- sandbox execution
- exact diff hashing
- exact commit approval binding
- task branches
- commits
- PR creation
- approved merge control
- rollback commits
- GitHub CI monitoring

## Approval Binding

AION-172 must invalidate approval after any code change and must bind approval to the exact proposal ID, commit SHA, diff hash, benchmark fingerprint, rollback commit, and deployment scope. It may not push to main, merge a different commit, or create a pull request before valid approval exists.

## Prohibited Scope

AION-172 may not implement direct main writes, force pushes, self-approval, protected-core edits under ordinary approval, dependency changes without exact authorization, test weakening, holdout mutation, automatic merge without approval, production deployment, model-weight modification, a v0.2 tag, a v0.2 release, or any modification to `aion-v0.1.0`.

Production GitHub calls remain disabled until explicitly configured. GitHub behavior must be adapter-driven and mocked in focused tests.
