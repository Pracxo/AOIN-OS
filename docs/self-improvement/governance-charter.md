# Governed Self-Improvement Governance Charter

Program: AION-SELF-IMPROVEMENT-001

Task: AION-165

## Purpose

AION-165 opens the governed self-improvement track after AION-164 merged persistent identity assertion replay protection. It closes `AION-163-PA-0007` as consumed by AION-164 and creates `AION-165-SI-0001` as the single active authorization for AION-166 governance-plane implementation.

The charter authorizes governance contracts, lifecycle validation, protected-core boundaries, approval binding, change budgets, risk classification, rollback requirements, and benchmark evidence requirements. It does not authorize source rewriting, Git mutation, pull request creation by AION, production canary activation, production deployment, or model-weight training.

## Runtime State

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

## Non-Negotiable Prohibitions

AION must never approve its own source changes, push directly to `main`, bypass GitHub checks, weaken tests to make a patch pass, alter protected governance controls inside an ordinary proposal, edit hidden holdout benchmarks through patch generation, activate production self-rewriting by default, create a v0.2 tag or release, alter `aion-v0.1.0`, or claim platform completion before AION-175 is merged and the repository is clean.

## Authorization

- `authorization_transaction_id=AION-165-SI-0001`
- `approval_record_id=AION-165-SI-0001`
- `parent_authorization_transaction_id=AION-163-PA-0007`
- `implementation_task=AION-166`
- `authorization_scope=governed-self-improvement-control-plane`
- `authorization_active=true`
- `authorization_consumed=false`
- `authorization_expired=false`
- `authorization_reusable=false`

## Required Evidence

Every future self-improvement proposal must carry immutable evidence references, a lifecycle state, a bounded risk assessment, a change budget decision, exact approval bindings when approval is requested, a rollback plan when required by risk, and benchmark evidence that cannot be weakened by the same candidate patch.
