#!/usr/bin/env python3
"""Validators for the AION self-improvement governance documents."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, cast

PROGRAM_ID = "AION-SELF-IMPROVEMENT-001"
ROOT_AUTHORIZATION_ID = "AION-163-PA-0007"
PARENT_AUTHORIZATION_ID = "AION-165-SI-0001"
EVALUATION_AUTHORIZATION_ID = "AION-167-SI-0002"
EXPERIMENT_AUTHORIZATION_ID = "AION-169-SI-0003"
AUTHORIZATION_ID = "AION-171-SI-0004"
CANARY_AUTHORIZATION_ID = "AION-173-SI-0005"
AION_166_FEATURE_COMMIT = "fae49a3f913b7a3d4d18ad4e7f989ed2aca5de91"
AION_166_MERGE_COMMIT = "9a7105e31b8f6e56faf53bfb56e11eed75a01203"
AION_167_FEATURE_COMMIT = "bbc04cf57f02483e00752c20fa70b77abf95ce46"
AION_167_MERGE_COMMIT = "98a50edb5eaaf55de5babaa0ea9eb057ef5b2feb"
AION_168_FEATURE_COMMIT = "8d1402f6c122098f3aec5809cf94539992b45d10"
AION_168_MERGE_COMMIT = "74472522edffbbeabb996c6d572dce1dcb0cda48"
AION_169_FEATURE_COMMIT = "3af4e7a24955f83f8e3d1e98d3fa26f008ad83e6"
AION_169_MERGE_COMMIT = "3a09cb642414ff22f15c90df41d1132030dbe0a1"
AION_170_FEATURE_COMMITS = (
    "2005217334301a6b4951cc3ae2a0d88de99b95e0",
    "4798459eec61e5f534c880234508815364804ee5",
)
AION_170_MERGE_COMMIT = "6e741c8327d900fa80480bce911fbccffb8b4781"
AION_171_FEATURE_COMMIT = "4970700555638b4ecd53a581d1797148906f81ef"
AION_171_MERGE_COMMIT = "478b79de1fbd4eeeb0280a41abf4050c0f513d8f"
AION_172_FEATURE_COMMIT = "4a8adbc6ed3c364588883eb5fe91e393f26479cd"
AION_172_MERGE_COMMIT = "0033f24c5f2f1f1b2a1a89a8595f29db1c1d1bf9"
AION_173_FEATURE_COMMIT = "bd215d2910e6c29b7f0d53381d0960330fda4623"
AION_173_MERGE_COMMIT = "9d827d8bbbe0cb726904b19b0662e214d7f1b04e"
AION_174_FEATURE_COMMIT = "61fdce1795385fa954114a38098f6f2dba26a5f4"
AION_174_MERGE_COMMIT = "dd17639986160938043d8ddef7da8cb9b8a2faa4"
AION_175_FEATURE_COMMIT = "50b498e9a47a95f82c26df718e11696b9ef741b3"
AION_175_MERGE_COMMIT = "00b71a6172fb136279716103b10dae986f455968"
AION_175_MERGED_AT = "2026-07-19T06:17:29Z"
AION_176_FEATURE_COMMIT = "1738f49ff22e197dd8fff3038fc8429306eadf76"
AION_176_MERGE_COMMIT = "ee50f1cc9ed3573661d1571954421abfb749e877"
AION_176_MERGED_AT = "2026-07-19T10:02:18Z"
AION_177_FEATURE_COMMIT = "b1f3f721038ffffe5d78115f7efe8da7f493b677"
AION_177_MERGE_COMMIT = "544c71ed18530699eb1756674d38c874af8a0aae"
AION_177_MERGED_AT = "2026-07-19T20:18:44Z"
AION_178_FEATURE_COMMIT = "1f7a9750e3b5567b173e9a42af069cb4d7d7bc8f"
AION_178_MERGE_COMMIT = "b05dd3cc49cff086997232bfc579a7ca891a184b"
AION_178_MERGED_AT = "2026-07-20T06:10:57Z"
AION_179_FEATURE_COMMITS = (
    "13fa892bf3dd4518fd9ea41ebaa58655813c6da9",
    "8246bef6bcdec313e07e0dff732239778fad3739",
)
AION_179_MERGE_COMMIT = "133040597ca8ed997bbc32b8bb8c980a123d2f9a"
AION_179_MERGED_AT = "2026-07-20T10:10:12Z"
OPERATOR_EVALUATION_ID = "AION-OE-001"
OPERATOR_EVALUATION_DECISION = (
    "OPERATOR_EVALUATION_PASS_RECOMMEND_SHADOW_MODE_AUTHORIZATION_REVIEW"
)
SHADOW_OPERATOR_EVALUATION_ID = "AION-SOE-001"
SHADOW_OPERATOR_EVALUATION_DECISION = (
    "SHADOW_MODE_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_ACTIVATION_AUTHORIZATION_REVIEW"
)
SHADOW_AUTHORIZATION_ID = "AION-177-SI-0006"
SHADOW_ACTIVATION_PHASE_ID = "AION-SELF-IMPROVEMENT-SHADOW-001"
SHADOW_CANDIDATE_ID = "controlled-self-improvement-shadow-mode"
SHADOW_WORKSTREAM = "self-improvement-shadow-observation"
SHADOW_IMPLEMENTATION_TASK = "AION-178"
SHADOW_OPERATOR_EVALUATION_TASK = "AION-179"
SHADOW_AUTHORIZATION_SCOPE = (
    "read-only-shadow-observation-evaluation-pattern-mining-proposal-generation"
)
SHADOW_ACTIVATION_AUTHORIZATION_ID = "AION-180-SI-0007"
SHADOW_ACTIVATION_PROGRAM_ID = (
    "AION-SELF-IMPROVEMENT-CONTROLLED-SHADOW-ACTIVATION-001"
)
SHADOW_ACTIVATION_CANDIDATE_ID = "controlled-shadow-mode-activation-control-plane"
SHADOW_ACTIVATION_WORKSTREAM = "self-improvement-shadow-activation-governance"
SHADOW_ACTIVATION_IMPLEMENTATION_TASK = "AION-181"
SHADOW_ACTIVATION_CLOSEOUT_TASK = "AION-182"
SHADOW_ACTIVATION_SCOPE = (
    "disabled-shadow-activation-request-approval-monitoring-deactivation-control-plane"
)

AION178_ALLOWED_CREATE = (
    "services/brain-api/src/aion_brain/contracts/self_improvement_shadow.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_mode.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_observation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_pipeline.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_evidence.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_budget.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_redaction.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_runner.py",
)

AION177_PROHIBITED_SOURCE_FILES = AION178_ALLOWED_CREATE

SHADOW_APPROVED_FLAGS = (
    "authorization_transaction_approved",
    "explicit_approval_record_approval",
    "implementation_authorization_approved",
    "implementation_go_status",
    "shadow_mode_contracts_approved",
    "shadow_observation_manifest_approved",
    "read_only_trace_reference_intake_approved",
    "read_only_evaluation_reference_intake_approved",
    "read_only_outcome_reference_intake_approved",
    "read_only_experience_reference_intake_approved",
    "redacted_metric_intake_approved",
    "deterministic_evaluation_invocation_approved",
    "failure_pattern_mining_approved",
    "bounded_hypothesis_generation_approved",
    "regression_test_proposal_generation_approved",
    "shadow_improvement_proposal_generation_approved",
    "operator_review_item_generation_approved",
    "shadow_evidence_bundle_approved",
    "shadow_audit_provenance_approved",
    "shadow_run_diagnostics_approved",
    "operator_invoked_batch_runner_approved",
    "explicit_manifest_input_approved",
    "ephemeral_shadow_store_approved",
    "operator_supplied_output_directory_approved",
    "resource_budget_enforcement_approved",
    "redaction_enforcement_approved",
    "retention_policy_approved",
    "deterministic_replay_approved",
    "shadow_drift_metrics_approved",
    "no_runtime_influence_enforcement_approved",
    "no_active_learning_promotion_enforcement_approved",
    "no_source_mutation_enforcement_approved",
    "no_git_mutation_enforcement_approved",
    "no_approval_creation_enforcement_approved",
    "test_only_fixture_approved",
    "documentation_and_static_evidence_approved",
)

SHADOW_PROHIBITED_FLAGS = (
    "implementation_no_go_status",
    "continuous_background_shadow_loop_approved",
    "production_event_stream_subscription_approved",
    "production_shadow_mode_activation_approved",
    "kernel_container_registration_approved",
    "application_startup_registration_approved",
    "background_scheduler_approved",
    "automatic_polling_approved",
    "network_call_approved",
    "external_connector_call_approved",
    "provider_sdk_approved",
    "raw_prompt_intake_approved",
    "hidden_reasoning_intake_approved",
    "credential_intake_approved",
    "token_intake_approved",
    "cookie_intake_approved",
    "private_key_intake_approved",
    "raw_user_message_intake_approved",
    "unredacted_personal_data_intake_approved",
    "source_patch_generation_approved",
    "source_file_mutation_approved",
    "canonical_repository_mutation_approved",
    "worktree_creation_approved",
    "git_branch_creation_approved",
    "git_commit_creation_approved",
    "git_push_approved",
    "real_pull_request_creation_approved",
    "approval_creation_approved",
    "approval_satisfaction_approved",
    "automatic_merge_approved",
    "manual_merge_execution_approved",
    "production_canary_approved",
    "production_deployment_approved",
    "model_weight_training_approved",
    "active_retrieval_weight_promotion_approved",
    "active_strategy_promotion_approved",
    "preference_promotion_approved",
    "skill_promotion_approved",
    "policy_mutation_approved",
    "audit_ledger_mutation_approved",
    "benchmark_manifest_mutation_approved",
    "holdout_mutation_approved",
    "holdout_disclosure_approved",
    "test_weakening_approved",
    "runtime_response_influence_approved",
    "runtime_planning_influence_approved",
    "runtime_retrieval_influence_approved",
    "runtime_policy_influence_approved",
    "runtime_tool_selection_influence_approved",
    "runtime_effect_approved",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "api_route_approved",
    "installed_cli_command_approved",
    "sdk_runtime_resource_approved",
    "v02_tag_created",
    "v02_release_created",
    "shadow_mode_runtime_enabled",
    "shadow_mode_source_rewrite_enabled",
    "shadow_mode_git_write_enabled",
    "shadow_mode_pr_creation_enabled",
    "shadow_mode_auto_merge_enabled",
    "shadow_mode_production_canary_enabled",
    "shadow_mode_deployment_enabled",
    "shadow_mode_provider_call_enabled",
    "shadow_mode_connector_runtime_enabled",
    "shadow_mode_model_training_enabled",
    "shadow_mode_approval_creation_enabled",
    "shadow_mode_self_approval_enabled",
    "shadow_mode_protected_core_bypass_enabled",
    "shadow_mode_user_traffic_enabled",
)

SHADOW_ALLOWED_INPUTS = (
    "trace reference IDs",
    "evaluation reference IDs",
    "outcome reference IDs",
    "experience reference IDs",
    "lesson reference IDs",
    "pattern reference IDs",
    "safe fingerprints",
    "redacted numeric metrics",
    "bounded timestamps",
    "synthetic test metadata",
    "operator-selected scope labels",
)

SHADOW_DISALLOWED_INPUTS = (
    "raw prompt",
    "raw hidden reasoning",
    "chain of thought",
    "raw user message",
    "credential",
    "token",
    "cookie",
    "authorization header",
    "private key",
    "provider payload",
    "raw source patch",
    "raw diff",
    "unredacted personal data",
    "arbitrary filesystem path",
    "URL",
    "network location",
    "executable command",
)

SHADOW_ALLOWED_OUTPUT_FLAGS = (
    "redacted observation summaries",
    "deterministic evaluation summaries",
    "repeated failure-pattern candidates",
    "bounded hypothesis candidates",
    "regression-test proposal specifications",
    "shadow improvement-proposal candidates",
    "operator review items",
    "audit evidence",
    "provenance evidence",
    "run diagnostics",
    "resource-budget evidence",
)

SHADOW_ALLOWED_REVIEW_STATES = (
    "shadow_observed",
    "shadow_evaluated",
    "shadow_pattern_detected",
    "shadow_hypothesis_generated",
    "shadow_regression_proposed",
    "shadow_proposal_generated",
    "operator_review_pending",
    "discarded",
    "archived",
)

SHADOW_FORBIDDEN_REVIEW_STATES = (
    "approved",
    "pr_created",
    "merged",
    "canary",
    "promoted",
)

SHADOW_RESOURCE_BUDGETS = {
    "maximum_observation_references": 1000,
    "maximum_evaluation_records": 1000,
    "maximum_failure_patterns": 100,
    "maximum_hypotheses": 50,
    "maximum_regression_test_proposals": 25,
    "maximum_shadow_proposals": 10,
    "maximum_concurrency": 4,
    "maximum_wall_clock_seconds": 1800,
    "maximum_benchmark_cost_units": 50,
    "maximum_output_bytes": 10485760,
    "maximum_operator_output_files": 20,
    "network_calls": 0,
    "git_operations": 0,
    "source_mutations": 0,
    "real_pull_requests": 0,
    "runtime_promotions": 0,
}

LIFECYCLE_STATES = (
    "observed",
    "hypothesized",
    "test_created",
    "experiment_ready",
    "patch_created",
    "sandbox_running",
    "sandbox_passed",
    "sandbox_failed",
    "approval_pending",
    "approved",
    "rejected",
    "pr_created",
    "merged",
    "canary",
    "promoted",
    "rolled_back",
    "archived",
)

ALLOWED_TRANSITIONS = {
    "observed": {"hypothesized", "archived"},
    "hypothesized": {"test_created", "rejected", "archived"},
    "test_created": {"experiment_ready", "rejected", "archived"},
    "experiment_ready": {"patch_created", "sandbox_failed", "rejected", "archived"},
    "patch_created": {"sandbox_running", "sandbox_failed", "archived"},
    "sandbox_running": {"sandbox_passed", "sandbox_failed"},
    "sandbox_passed": {"approval_pending", "archived"},
    "sandbox_failed": {"hypothesized", "rejected", "archived"},
    "approval_pending": {"approved", "rejected", "archived"},
    "approved": {"pr_created", "archived"},
    "rejected": {"archived"},
    "pr_created": {"merged", "rejected", "archived"},
    "merged": {"canary", "archived"},
    "canary": {"promoted", "rolled_back"},
    "promoted": {"archived"},
    "rolled_back": {"archived"},
    "archived": set(),
}

GOVERNANCE_FALSE_FLAGS = {
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "automatic_merge_enabled",
    "automatic_production_deployment_enabled",
    "source_rewriting_enabled",
    "source_mutation_enabled",
    "git_commits_enabled",
    "branch_creation_enabled",
    "pull_request_creation_enabled",
    "merge_enabled",
    "automatic_approval_enabled",
    "benchmark_mutation_by_candidate_enabled",
    "holdout_disclosure_to_patch_generators_enabled",
    "production_deployment_enabled",
    "deployment_enabled",
    "model_weight_training_enabled",
    "model_weight_changes_enabled",
    "canary_runtime_enabled",
    "production_canary_enabled",
    "production_exposure_enabled",
    "unrestricted_traffic_exposure_enabled",
    "automatic_protected_core_modification_enabled",
    "automatic_policy_relaxation_enabled",
    "runtime_self_approval_enabled",
    "autonomous_production_activation_enabled",
}

GOVERNANCE_TRUE_FLAGS = {
    "human_approval_required",
    "exact_commit_approval_required",
    "exact_diff_hash_approval_required",
    "no_self_approval",
    "protected_core_dual_approval_required",
    "rollback_plan_required",
    "benchmark_evidence_required",
    "hidden_holdout_required",
    "failure_pattern_intake_authorized",
    "improvement_hypotheses_authorized",
    "regression_test_proposals_authorized",
    "experiment_plans_authorized",
    "baseline_candidate_experiment_execution_authorized",
    "risk_classification_authorized",
    "evidence_bundles_authorized",
    "approval_pending_lifecycle_authorized",
    "isolated_git_worktrees_authorized",
    "bounded_file_edits_authorized",
    "test_first_patch_workflow_authorized",
    "sandbox_execution_authorized",
    "exact_diff_hashing_authorized",
    "exact_commit_approval_binding_authorized",
    "task_branches_authorized",
    "commits_authorized",
    "pull_request_creation_authorized",
    "approved_merge_control_authorized",
    "rollback_commits_authorized",
    "github_ci_monitoring_authorized",
    "canary_plans_authorized",
    "exposure_budgets_authorized",
    "monitoring_windows_authorized",
    "automatic_rollback_under_approved_thresholds_authorized",
    "improvement_outcome_ledger_authorized",
    "retrieval_ranking_optimization_authorized",
    "case_based_planning_authorized",
    "bounded_strategy_selection_authorized",
    "shadow_mode_policy_comparison_authorized",
    "data_only_procedural_skill_evolution_authorized",
    "final_integrated_dry_run_authorized",
    "self_improvement_platform_implemented",
    "proposal_generation_available",
    "experiment_execution_available",
    "benchmark_comparison_available",
    "isolated_worktree_available",
    "test_first_patch_generation_available",
    "approval_bound_pr_creation_available",
    "approval_bound_merge_control_available",
    "canary_simulation_available",
    "automatic_rollback_available",
    "adaptive_retrieval_candidates_available",
    "case_based_planning_candidates_available",
    "procedural_skill_candidates_available",
    "holdout_protected",
    "rollback_required",
}

PROTECTED_PATHS = (
    ".github/workflows/",
    "scripts/*approval*",
    "scripts/*no-go*",
    "scripts/*release*",
    "scripts/lib/*authorization*",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/self_improvement/approval*",
    "services/brain-api/src/aion_brain/self_improvement/protected*",
    "docs/self-improvement/holdout/",
    "docs/self-improvement/policy/",
)

CHANGE_BUDGET_DIMENSIONS = (
    "maximum files",
    "maximum insertions",
    "maximum deletions",
    "maximum dependency changes",
    "maximum protected paths",
    "maximum benchmark cost",
    "maximum canary exposure",
)

RISK_LEVELS = ("low", "medium", "high", "critical")

EVALUATION_APPROVED_SCOPE = (
    "benchmark contracts",
    "baseline results",
    "candidate results",
    "multi-objective scoring",
    "hard safety gates",
    "immutable benchmark manifests",
    "holdout references",
    "statistical comparison",
    "evaluation provenance",
    "cost and latency accounting",
    "benchmark drift detection",
)

EVALUATION_PROHIBITED_SCOPE = (
    "source rewriting",
    "Git mutation",
    "pull request creation",
    "automatic approval",
    "benchmark mutation through candidate code",
    "holdout disclosure to patch generators",
    "production deployment",
    "model-weight training",
    "v0.2 tag or release",
    "aion-v0.1.0 modification",
)

EXPERIMENT_APPROVED_SCOPE = (
    "failure-pattern intake",
    "improvement hypotheses",
    "regression-test proposals",
    "experiment plans",
    "baseline/candidate experiment execution",
    "risk classification",
    "evidence bundles",
    "approval-pending lifecycle",
)

EXPERIMENT_PROHIBITED_SCOPE = (
    "source mutation",
    "source rewriting",
    "Git commits",
    "branch creation",
    "Git mutation",
    "pull request creation",
    "merge",
    "production deployment",
    "deployment",
    "model-weight changes",
    "model-weight training",
    "automatic approval",
    "v0.2 tag or release",
    "aion-v0.1.0 modification",
)

REWRITE_APPROVED_SCOPE = (
    "ephemeral Git worktrees",
    "bounded file edits",
    "test-first patch workflow",
    "sandbox execution",
    "exact diff hashing",
    "exact commit approval binding",
    "task branches",
    "commits",
    "PR creation",
    "approved merge control",
    "rollback commits",
    "GitHub CI monitoring",
)

REWRITE_PROHIBITED_SCOPE = (
    "direct main writes",
    "force pushes",
    "self-approval",
    "protected-core edits under ordinary approval",
    "dependency changes without exact authorization",
    "test weakening",
    "holdout mutation",
    "automatic merge without approval",
    "production deployment",
    "model-weight modification",
    "v0.2 tag or release",
    "aion-v0.1.0 modification",
)

APPROVAL_BINDING_REQUIREMENTS = (
    "proposal ID",
    "exact commit SHA",
    "exact diff hash",
    "exact benchmark fingerprint",
    "exact rollback commit",
    "exact deployment scope",
)

TEST_WEAKENING_CONTROLS = (
    "detect deleted assertions",
    "detect reduced expected security state",
    "detect skipped tests",
    "detect broad test exclusions",
    "detect changed benchmark thresholds",
    "require elevated approval when source and guarding tests both change",
    "mutation-style checks for high-risk proposals",
)

CANARY_APPROVED_SCOPE = (
    "canary plans",
    "exposure budgets",
    "monitoring windows",
    "automatic rollback under approved thresholds",
    "improvement outcome ledger",
    "retrieval-ranking optimization",
    "case-based planning",
    "bounded strategy selection",
    "shadow-mode policy comparison",
    "data-only procedural skill evolution",
    "final integrated dry-run",
)

CANARY_PROHIBITED_SCOPE = (
    "production canary by default",
    "unrestricted traffic exposure",
    "model-weight training",
    "automatic protected-core modification",
    "automatic policy relaxation",
    "runtime self-approval",
    "autonomous production activation",
    "v0.2 tag or release",
    "aion-v0.1.0 modification",
)

SHADOW_APPROVED_SCOPE = (
    "shadow-mode contracts",
    "shadow observation manifest",
    "read-only trace reference intake",
    "read-only evaluation reference intake",
    "read-only outcome reference intake",
    "read-only experience reference intake",
    "redacted metric intake",
    "deterministic evaluation invocation",
    "failure-pattern mining",
    "bounded hypothesis generation",
    "regression-test proposal generation",
    "shadow improvement-proposal generation",
    "operator review item generation",
    "shadow evidence bundle",
    "shadow audit provenance",
    "shadow run diagnostics",
    "operator-invoked batch runner",
    "explicit manifest input",
    "ephemeral shadow store",
    "operator-supplied output directory",
    "resource budget enforcement",
    "redaction enforcement",
    "retention policy",
    "deterministic replay",
    "shadow drift metrics",
    "no runtime influence enforcement",
    "no active learning promotion enforcement",
    "no source mutation enforcement",
    "no Git mutation enforcement",
    "no approval creation enforcement",
    "test-only fixture",
    "documentation and static evidence",
)

SHADOW_PROHIBITED_SCOPE = (
    "continuous background shadow loop",
    "production event stream subscription",
    "production shadow-mode activation",
    "kernel container registration",
    "application startup registration",
    "background scheduler",
    "automatic polling",
    "network calls",
    "external connector calls",
    "provider SDKs",
    "raw prompt intake",
    "hidden reasoning intake",
    "credential intake",
    "token intake",
    "cookie intake",
    "private key intake",
    "raw user message intake",
    "unredacted personal data intake",
    "source patch generation",
    "source file mutation",
    "canonical repository mutation",
    "worktree creation",
    "Git branch creation",
    "Git commit creation",
    "Git push",
    "real pull request creation",
    "approval creation",
    "approval satisfaction",
    "automatic merge",
    "manual merge execution",
    "production canary",
    "production deployment",
    "model-weight training",
    "active retrieval weight promotion",
    "active strategy promotion",
    "preference promotion",
    "skill promotion",
    "policy mutation",
    "audit ledger mutation",
    "benchmark manifest mutation",
    "holdout mutation",
    "holdout disclosure",
    "test weakening",
    "runtime response influence",
    "runtime planning influence",
    "runtime retrieval influence",
    "runtime policy influence",
    "runtime tool-selection influence",
    "runtime effect",
    "dependency change",
    "migration",
    "GitHub workflow change",
    "API route",
    "installed CLI command",
    "SDK runtime resource",
    "v0.2 tag or release",
)

CANARY_APPROVAL_BINDING_REQUIREMENTS = (
    "exact merge commit",
    "exact deployment artifact",
    "exact exposure budget",
    "exact monitoring duration",
    "exact rollback commit",
    "exact metric thresholds",
    "exact outcome ledger ID",
    "exact adaptive policy version",
)

REQUIRED_DOCS = (
    "docs/self-improvement/governance-charter.md",
    "docs/self-improvement/evaluation-authorization.md",
    "docs/self-improvement/experiment-authorization.md",
    "docs/self-improvement/rewrite-authorization.md",
    "docs/self-improvement/canary-authorization.md",
    "docs/self-improvement/final-architecture.md",
    "docs/self-improvement/operator-evaluation-guide.md",
    "docs/self-improvement/security-review.md",
    "docs/self-improvement/benchmark-report.md",
    "docs/self-improvement/end-to-end-evidence.md",
    "docs/self-improvement/known-limitations.md",
    "docs/self-improvement/runtime-activation-checklist.md",
    "docs/self-improvement/future-model-training-boundary.md",
    "docs/self-improvement/aion-176-post-merge-evidence-reconciliation.md",
    "docs/self-improvement/protected-core-boundary.md",
    "docs/self-improvement/approval-model.md",
    "docs/self-improvement/change-budget-model.md",
    "docs/self-improvement/risk-model.md",
    "docs/self-improvement/aion-164-closeout-evidence.md",
    "docs/self-improvement/authorization-ledger.json",
    "docs/self-improvement/program-ledger.json",
    "docs/adr/0156-governed-self-improvement-control-plane.md",
    "docs/adr/0157-self-improvement-evaluation-authorization.md",
    "docs/adr/0158-self-improvement-experiment-authorization.md",
    "docs/adr/0159-self-improvement-rewrite-authorization.md",
    "docs/adr/0160-self-improvement-canary-authorization.md",
    "docs/adr/0161-governed-self-improvement-platform-complete.md",
)

AION177_REQUIRED_DOCS = (
    "docs/self-improvement/operator-evaluation-closeout.md",
    "docs/self-improvement/shadow-mode-architecture.md",
    "docs/self-improvement/shadow-mode-boundary.md",
    "docs/self-improvement/shadow-mode-data-governance.md",
    "docs/self-improvement/shadow-mode-resource-budgets.md",
    "docs/self-improvement/shadow-mode-threat-model.md",
    "docs/self-improvement/shadow-mode-operator-workflow.md",
    "docs/self-improvement/shadow-mode-roadmap.md",
    "docs/release/self-improvement-shadow-mode-authorization-transaction.md",
    "docs/release/self-improvement-shadow-mode-explicit-approval-record.md",
    "docs/release/self-improvement-shadow-mode-scope.md",
    "docs/release/self-improvement-shadow-mode-runtime-hold.md",
    "docs/release/self-improvement-shadow-mode-no-go.md",
    "docs/release/self-improvement-shadow-mode-checklist.md",
    "docs/release/self-improvement-shadow-mode-evidence-matrix.md",
    "docs/adr/0162-controlled-self-improvement-shadow-mode-authorization.md",
)

AION177_REQUIRED_EXAMPLES = (
    "examples/self-improvement/operator-evaluation-closeout.json",
    "examples/self-improvement/shadow-mode-authorization.json",
    "examples/self-improvement/shadow-mode-runtime-hold.json",
    "examples/self-improvement/shadow-mode-resource-budget.json",
    "examples/self-improvement/shadow-mode-data-boundary.json",
    "examples/self-improvement/shadow-mode-output-boundary.json",
    "examples/self-improvement/shadow-mode-operator-review-item.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-authorization.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-runtime-hold.json",
)

AION178_REQUIRED_DOCS = (
    "docs/self-improvement/shadow-mode-implementation.md",
    "docs/self-improvement/shadow-mode-reference-adapters.md",
    "docs/self-improvement/shadow-mode-pipeline.md",
    "docs/self-improvement/shadow-mode-evidence.md",
    "docs/self-improvement/shadow-mode-output-and-retention.md",
    "docs/self-improvement/shadow-mode-operator-runbook.md",
    "docs/self-improvement/shadow-mode-security-review.md",
    "docs/self-improvement/aion-178-checklist.md",
    "docs/release/self-improvement-shadow-mode-implementation.md",
    "docs/release/self-improvement-shadow-mode-security-evidence.md",
    "docs/release/self-improvement-shadow-mode-implementation-runtime-hold.md",
    "docs/release/self-improvement-shadow-mode-implementation-no-go.md",
    "docs/release/self-improvement-shadow-mode-implementation-checklist.md",
    "docs/release/self-improvement-shadow-mode-implementation-evidence-matrix.md",
    "docs/adr/0163-controlled-self-improvement-shadow-mode-plane.md",
)

AION178_REQUIRED_EXAMPLES = (
    "examples/self-improvement/shadow-observation-manifest.json",
    "examples/self-improvement/shadow-reference-snapshot.json",
    "examples/self-improvement/shadow-evaluation-summary.json",
    "examples/self-improvement/shadow-failure-pattern.json",
    "examples/self-improvement/shadow-hypothesis.json",
    "examples/self-improvement/shadow-regression-test-proposal.json",
    "examples/self-improvement/shadow-improvement-proposal.json",
    "examples/self-improvement/shadow-operator-review-item.json",
    "examples/self-improvement/shadow-budget-failure.json",
    "examples/self-improvement/shadow-run-diagnostics.json",
    "examples/self-improvement/shadow-evidence-bundle.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-plane.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-review-items.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-runtime-hold.json",
)

AION179_REQUIRED_DOCS = (
    "docs/self-improvement/shadow-mode-operator-evaluation-closeout.md",
    "docs/self-improvement/shadow-mode-operator-evaluation-report.md",
    "docs/self-improvement/shadow-mode-evaluation-scenarios.md",
    "docs/self-improvement/shadow-mode-activation-decision-boundary.md",
    "docs/release/self-improvement-shadow-mode-evaluation-closeout.md",
    "docs/release/self-improvement-shadow-mode-evaluation-checklist.md",
    "docs/release/self-improvement-shadow-mode-evaluation-evidence-matrix.md",
    "docs/release/self-improvement-shadow-mode-evaluation-runtime-hold.md",
    "docs/adr/0164-controlled-shadow-mode-operator-evaluation.md",
)

AION179_REQUIRED_EXAMPLES = (
    "examples/self-improvement/shadow-mode-operator-evaluation-report.json",
    "examples/self-improvement/shadow-mode-operator-evaluation-scenario-summary.json",
    "examples/self-improvement/shadow-mode-activation-review-boundary.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-operator-evaluation.json",
    "operator-console-static/demo-data/self-improvement-shadow-mode-activation-review-boundary.json",
)

AION180_REQUIRED_DOCS = (
    "docs/self-improvement/aion-179-delivery-verification.md",
    "docs/self-improvement/shadow-activation-control-plane-architecture.md",
    "docs/self-improvement/shadow-activation-authorization-boundary.md",
    "docs/self-improvement/shadow-activation-approval-binding.md",
    "docs/self-improvement/shadow-activation-data-boundary.md",
    "docs/self-improvement/shadow-activation-resource-budgets.md",
    "docs/self-improvement/shadow-activation-monitoring.md",
    "docs/self-improvement/shadow-activation-deactivation.md",
    "docs/self-improvement/shadow-activation-threat-model.md",
    "docs/self-improvement/shadow-activation-roadmap.md",
    "docs/release/self-improvement-shadow-activation-authorization-transaction.md",
    "docs/release/self-improvement-shadow-activation-explicit-approval-record.md",
    "docs/release/self-improvement-shadow-activation-scope.md",
    "docs/release/self-improvement-shadow-activation-runtime-hold.md",
    "docs/release/self-improvement-shadow-activation-no-go.md",
    "docs/release/self-improvement-shadow-activation-checklist.md",
    "docs/release/self-improvement-shadow-activation-evidence-matrix.md",
    "docs/adr/0165-controlled-shadow-activation-control-plane-authorization.md",
)

AION180_REQUIRED_EXAMPLES = (
    "examples/self-improvement/shadow-activation-authorization.json",
    "examples/self-improvement/shadow-activation-candidate.json",
    "examples/self-improvement/shadow-activation-request.json",
    "examples/self-improvement/shadow-activation-approval-binding.json",
    "examples/self-improvement/shadow-activation-resource-budget.json",
    "examples/self-improvement/shadow-activation-monitoring-plan.json",
    "examples/self-improvement/shadow-activation-deactivation-plan.json",
    "examples/self-improvement/shadow-activation-runtime-hold.json",
    "operator-console-static/demo-data/self-improvement-shadow-activation-authorization.json",
    "operator-console-static/demo-data/self-improvement-shadow-activation-runtime-hold.json",
)

SHADOW_ACTIVATION_APPROVED_FLAGS = (
    "authorization_transaction_approved",
    "explicit_approval_record_approval",
    "implementation_authorization_approved",
    "implementation_go_status",
    "shadow_activation_contracts_approved",
    "shadow_activation_request_contract_approved",
    "shadow_activation_candidate_contract_approved",
    "shadow_activation_state_machine_approved",
    "shadow_activation_evidence_bundle_approved",
    "shadow_activation_exact_commit_binding_approved",
    "shadow_activation_exact_tree_binding_approved",
    "shadow_activation_exact_diff_binding_approved",
    "shadow_activation_evaluation_fingerprint_binding_approved",
    "shadow_activation_benchmark_manifest_binding_approved",
    "shadow_activation_benchmark_result_binding_approved",
    "shadow_activation_reference_set_binding_approved",
    "shadow_activation_operator_principal_binding_approved",
    "shadow_activation_output_boundary_binding_approved",
    "shadow_activation_retention_binding_approved",
    "shadow_activation_run_budget_binding_approved",
    "shadow_activation_monitoring_threshold_binding_approved",
    "shadow_activation_deactivation_plan_binding_approved",
    "shadow_activation_expiry_binding_approved",
    "shadow_activation_non_reuse_enforcement_approved",
    "shadow_activation_separation_of_duties_approved",
    "shadow_activation_security_review_contract_approved",
    "shadow_activation_data_classification_contract_approved",
    "shadow_activation_allowed_adapter_registry_approved",
    "shadow_activation_local_evidence_bundle_adapter_approved",
    "shadow_activation_in_memory_adapter_approved",
    "shadow_activation_fail_closed_validation_approved",
    "shadow_activation_kill_switch_contract_approved",
    "shadow_activation_health_check_contract_approved",
    "shadow_activation_monitoring_plan_approved",
    "shadow_activation_deactivation_plan_approved",
    "shadow_activation_incident_record_approved",
    "shadow_activation_audit_provenance_approved",
    "shadow_activation_diagnostics_approved",
    "shadow_activation_simulation_approved",
    "shadow_activation_operator_review_item_approved",
    "shadow_activation_test_only_fixture_approved",
    "shadow_activation_documentation_and_static_evidence_approved",
    "shadow_activation_no_runtime_enablement_enforcement_approved",
    "shadow_activation_no_source_mutation_enforcement_approved",
    "shadow_activation_no_git_mutation_enforcement_approved",
    "shadow_activation_no_pr_creation_enforcement_approved",
    "shadow_activation_no_approval_creation_enforcement_approved",
    "shadow_activation_no_promotion_enforcement_approved",
    "shadow_activation_no_production_exposure_enforcement_approved",
)

SHADOW_ACTIVATION_PROHIBITED_FLAGS = (
    "implementation_no_go_status",
    "shadow_activation_enabled",
    "shadow_mode_runtime_enabled",
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "production_shadow_mode_enabled",
    "production_event_stream_subscription_enabled",
    "kernel_container_registration_enabled",
    "application_startup_registration_enabled",
    "background_scheduler_enabled",
    "automatic_polling_enabled",
    "continuous_background_loop_enabled",
    "network_calls_enabled",
    "connector_calls_enabled",
    "provider_calls_enabled",
    "model_calls_enabled",
    "raw_prompt_intake_enabled",
    "hidden_reasoning_intake_enabled",
    "raw_user_message_intake_enabled",
    "credential_intake_enabled",
    "token_intake_enabled",
    "cookie_intake_enabled",
    "private_key_intake_enabled",
    "unredacted_personal_data_intake_enabled",
    "source_patch_generation_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_branch_creation_enabled",
    "git_commit_creation_enabled",
    "git_push_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "approval_satisfaction_enabled",
    "automatic_merge_enabled",
    "manual_merge_execution_enabled",
    "active_retrieval_promotion_enabled",
    "active_strategy_promotion_enabled",
    "preference_promotion_enabled",
    "skill_promotion_enabled",
    "policy_mutation_enabled",
    "audit_ledger_mutation_enabled",
    "benchmark_manifest_mutation_enabled",
    "benchmark_threshold_mutation_enabled",
    "holdout_mutation_enabled",
    "holdout_disclosure_enabled",
    "test_weakening_enabled",
    "runtime_response_influence_enabled",
    "runtime_retrieval_influence_enabled",
    "runtime_planning_influence_enabled",
    "runtime_policy_influence_enabled",
    "runtime_tool_selection_influence_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_traffic_exposure_enabled",
    "runtime_effect_enabled",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "api_route_approved",
    "installed_cli_command_approved",
    "sdk_runtime_resource_approved",
    "v02_tag_created",
    "v02_release_created",
)

SHADOW_ACTIVATION_ALLOWED_CREATE = (
    "services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py",
    "services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py",
)

SHADOW_ACTIVATION_ALLOWED_UPDATE = (
    "services/brain-api/src/aion_brain/self_improvement/__init__.py",
)

SHADOW_ACTIVATION_REQUIRED_CANDIDATE_FIELDS = (
    "activation_candidate_id",
    "program_id",
    "activation_program_id",
    "implementation_authorization_id",
    "parent_evaluation_id",
    "parent_evaluation_decision",
    "base_commit_sha",
    "candidate_commit_sha",
    "candidate_tree_sha",
    "diff_sha256",
    "implementation_evidence_fingerprint",
    "evaluation_report_fingerprint",
    "benchmark_manifest_fingerprint",
    "benchmark_result_fingerprint",
    "reference_set_fingerprint",
    "operator_scope_fingerprint",
    "output_boundary_fingerprint",
    "run_budget_fingerprint",
    "monitoring_plan_fingerprint",
    "deactivation_plan_fingerprint",
    "rollback_commit_sha",
    "risk_level",
    "created_at",
    "expires_at",
)

SHADOW_ACTIVATION_REQUIRED_REQUEST_FIELDS = (
    "activation_request_id",
    "activation_candidate",
    "requesting_operator_principal_id",
    "requested_environment",
    "data_classification",
    "allowed_reference_kinds",
    "approved_reference_fingerprints",
    "approved_adapter_types",
    "maximum_runs",
    "activation_window_start",
    "activation_window_end",
    "resource_budget",
    "monitoring_plan",
    "deactivation_plan",
    "output_boundary",
    "retention_seconds",
    "operator_review_required",
    "runtime_activation_requested",
    "created_at",
)

SHADOW_ACTIVATION_APPROVAL_BINDING_FIELDS = (
    "activation_request_id",
    "activation_candidate_id",
    "base_commit_sha",
    "candidate_commit_sha",
    "candidate_tree_sha",
    "diff_sha256",
    "implementation_evidence_fingerprint",
    "evaluation_report_fingerprint",
    "benchmark_manifest_fingerprint",
    "benchmark_result_fingerprint",
    "reference_set_fingerprint",
    "operator_scope_fingerprint",
    "output_boundary_fingerprint",
    "run_budget_fingerprint",
    "monitoring_plan_fingerprint",
    "deactivation_plan_fingerprint",
    "rollback_commit_sha",
    "requesting_operator_principal_id",
    "approver_principal_ids",
    "security_reviewer_principal_ids",
    "activation_window_start",
    "activation_window_end",
    "maximum_runs",
    "approved_adapter_types",
    "approved_reference_fingerprints",
    "approved_environment",
    "approved_at",
    "expires_at",
    "consumed",
    "reusable",
)

SHADOW_ACTIVATION_ALLOWED_OUTCOMES = (
    "candidate_valid",
    "candidate_invalid",
    "approval_required",
    "approval_invalid",
    "simulation_ready",
    "simulation_passed",
    "simulation_failed",
    "expired",
    "revoked",
    "archived",
    "runtime_disabled",
)

SHADOW_ACTIVATION_STATES = (
    "drafted",
    "evidence_ready",
    "approval_pending",
    "approved_disabled",
    "simulation_ready",
    "simulated",
    "review_pending",
    "rejected",
    "expired",
    "revoked",
    "archived",
)

SHADOW_ACTIVATION_ALLOWED_TRANSITIONS = {
    "drafted": {"evidence_ready", "rejected", "archived"},
    "evidence_ready": {"approval_pending", "rejected", "archived"},
    "approval_pending": {"approved_disabled", "rejected", "expired", "revoked"},
    "approved_disabled": {"simulation_ready", "expired", "revoked", "archived"},
    "simulation_ready": {"simulated", "rejected", "expired", "revoked"},
    "simulated": {"review_pending", "rejected", "archived"},
    "review_pending": {"archived", "revoked"},
    "rejected": {"archived"},
    "expired": {"archived"},
    "revoked": {"archived"},
    "archived": set(),
}

SHADOW_ACTIVATION_FORBIDDEN_STATES = (
    "active",
    "running_in_production",
    "canary",
    "deployed",
    "promoted",
    "merged",
    "self_approved",
)

SHADOW_ACTIVATION_RESOURCE_LIMITS = {
    "maximum_activation_window_seconds": 3600,
    "maximum_runs_per_activation": 10,
    "maximum_observation_references_per_run": 1000,
    "maximum_evaluation_records_per_run": 1000,
    "maximum_failure_patterns_per_run": 100,
    "maximum_hypotheses_per_run": 50,
    "maximum_regression_test_proposals_per_run": 25,
    "maximum_shadow_proposals_per_run": 10,
    "maximum_concurrency": 4,
    "maximum_wall_clock_seconds_per_run": 1800,
    "maximum_benchmark_cost_units_per_run": 50,
    "maximum_output_bytes_per_run": 10485760,
    "maximum_total_output_bytes_per_activation": 52428800,
    "maximum_operator_output_files_per_run": 20,
    "maximum_retention_seconds": 604800,
    "production_exposure_basis_points": 0,
    "network_calls": 0,
    "connector_calls": 0,
    "provider_calls": 0,
    "git_operations": 0,
    "source_mutations": 0,
    "real_pull_requests": 0,
    "approvals_created": 0,
    "merges": 0,
    "runtime_promotions": 0,
    "production_canaries": 0,
    "deployments": 0,
    "model_training_runs": 0,
}

SHADOW_ACTIVATION_MONITORED_VALUES = (
    "run_count",
    "reference_count",
    "evaluation_count",
    "pattern_count",
    "hypothesis_count",
    "regression_proposal_count",
    "shadow_proposal_count",
    "review_item_count",
    "budget_violation_count",
    "redaction_failure_count",
    "reference_failure_count",
    "fingerprint_mismatch_count",
    "output_boundary_failure_count",
    "wall_clock_seconds",
    "benchmark_cost_units",
    "output_bytes",
    "output_files",
    "network_call_count",
    "git_operation_count",
    "source_mutation_count",
    "real_pr_count",
    "approval_creation_count",
    "runtime_promotion_count",
    "runtime_influence_count",
)

SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS = (
    "any network call",
    "any connector call",
    "any provider call",
    "any Git operation",
    "any source mutation",
    "any PR creation",
    "any approval creation",
    "any runtime promotion",
    "any runtime influence",
    "any output-boundary escape",
    "any redaction failure",
    "any holdout disclosure",
    "any protected-material exposure",
    "any fingerprint mismatch",
    "any budget violation",
    "any unknown reference type",
    "any stale or expired approval",
    "activation window expiry",
    "run-count exhaustion",
    "operator kill switch",
)

SHADOW_ACTIVATION_THREATS = (
    "evaluation PASS mistaken for activation approval",
    "AION-177-SI-0006 reuse",
    "AION-180-SI-0007 mistaken for runtime activation authority",
    "forged activation candidate",
    "changed candidate commit after approval",
    "changed diff after approval",
    "changed benchmark evidence after approval",
    "changed reference set after approval",
    "changed output boundary after approval",
    "changed run budget after approval",
    "changed monitoring thresholds after approval",
    "changed deactivation plan after approval",
    "stale approval",
    "replayed approval",
    "self-approval",
    "duplicate approvers",
    "operator identity spoofing",
    "security reviewer spoofing",
    "reference bundle substitution",
    "local file path traversal",
    "symlink escape",
    "hidden file input",
    "oversized evidence bundle",
    "unredacted request-material smuggling",
    "private reasoning-material smuggling",
    "credential or token smuggling",
    "personal-data leakage",
    "source-patch smuggling",
    "raw-diff smuggling",
    "output directory escape",
    "reference flooding",
    "proposal flooding",
    "budget bypass",
    "runtime influence",
    "active-learning promotion",
    "network fallback",
    "background activation",
    "production event subscription",
    "activation outside the approved time window",
    "run-count overrun",
    "deactivation suppression",
    "evidence deletion",
    "activation evidence mistaken for implementation approval",
    "production activation without another authorization",
)

PRIVATE_MARKERS = (
    "raw prompt",
    "raw_prompt",
    "hidden reasoning",
    "hidden_reasoning",
    "chain-of-thought",
    "chain_of_thought",
    "credential_secret",
    "access_token",
    "refresh_token",
)


class GovernanceValidationError(ValueError):
    """Raised when a governance evidence artifact is invalid."""


@dataclass(frozen=True)
class TransitionDecision:
    current_state: str
    next_state: str
    allowed: bool
    reason: str


def validate_transition(current_state: str, next_state: str) -> TransitionDecision:
    if current_state not in ALLOWED_TRANSITIONS:
        return TransitionDecision(current_state, next_state, False, "unknown current state")
    if next_state not in LIFECYCLE_STATES:
        return TransitionDecision(current_state, next_state, False, "unknown next state")
    if next_state not in ALLOWED_TRANSITIONS[current_state]:
        return TransitionDecision(current_state, next_state, False, "unknown lifecycle transition")
    return TransitionDecision(current_state, next_state, True, "allowed lifecycle transition")


def require_transition(current_state: str, next_state: str) -> TransitionDecision:
    decision = validate_transition(current_state, next_state)
    if not decision.allowed:
        raise GovernanceValidationError(decision.reason)
    return decision


def validate_sequence(states: Iterable[str]) -> tuple[TransitionDecision, ...]:
    state_list = tuple(states)
    decisions = []
    for current_state, next_state in zip(state_list, state_list[1:]):
        decisions.append(require_transition(current_state, next_state))
    return tuple(decisions)


def validate_repo(repo_root: Path) -> None:
    repo_root = repo_root.resolve()
    _require_required_docs(repo_root)
    _validate_adr_index(repo_root)
    authorization = _load_json(repo_root / "docs/self-improvement/authorization-ledger.json")
    program = _load_json(repo_root / "docs/self-improvement/program-ledger.json")
    validate_authorization_ledger(authorization)
    validate_program_ledger(program)
    validate_operator_evaluation_closeout(
        _load_json(repo_root / "examples/self-improvement/operator-evaluation-closeout.json")
    )
    validate_shadow_authorization_example(
        _load_json(repo_root / "examples/self-improvement/shadow-mode-authorization.json")
    )
    validate_shadow_runtime_hold_example(
        _load_json(repo_root / "examples/self-improvement/shadow-mode-runtime-hold.json")
    )
    validate_shadow_operator_evaluation_report(
        _load_json(repo_root / "examples/self-improvement/shadow-mode-operator-evaluation-report.json")
    )
    validate_shadow_activation_authorization_example(
        _load_json(repo_root / "examples/self-improvement/shadow-activation-authorization.json")
    )
    validate_shadow_activation_runtime_hold_example(
        _load_json(repo_root / "examples/self-improvement/shadow-activation-runtime-hold.json")
    )
    _validate_docs_do_not_store_private_material(repo_root)


def validate_no_go(repo_root: Path) -> None:
    authorization = _load_json(repo_root / "docs/self-improvement/authorization-ledger.json")
    active = _current_authorization_record(authorization)
    if active.get("authorization_transaction_id") == SHADOW_ACTIVATION_AUTHORIZATION_ID:
        _validate_shadow_activation_authorization_record(active)
        return
    false_keys = set(GOVERNANCE_FALSE_FLAGS)
    false_keys.update(SHADOW_PROHIBITED_FLAGS)
    for key in false_keys:
        if active.get(key) is not False:
            raise GovernanceValidationError(f"{key} must be false")
    for key in SHADOW_APPROVED_FLAGS:
        if active.get(key) is not True:
            raise GovernanceValidationError(f"{key} must be true")
    required_prohibited_scope: tuple[str, ...]
    if active.get("authorization_transaction_id") == SHADOW_AUTHORIZATION_ID:
        required_prohibited_scope = SHADOW_PROHIBITED_SCOPE
    elif active.get("authorization_transaction_id") == CANARY_AUTHORIZATION_ID:
        required_prohibited_scope = CANARY_PROHIBITED_SCOPE
    elif active.get("authorization_transaction_id") == AUTHORIZATION_ID:
        required_prohibited_scope = REWRITE_PROHIBITED_SCOPE
    else:
        required_prohibited_scope = EXPERIMENT_PROHIBITED_SCOPE
    for item in required_prohibited_scope:
        if item not in active.get("prohibited_scope", []):
            raise GovernanceValidationError(f"{item} must be prohibited")
    if active.get("shadow_mode_implemented") is True:
        for relative in AION178_ALLOWED_CREATE:
            if not (repo_root / relative).is_file():
                raise GovernanceValidationError(f"AION-178 runtime source must exist: {relative}")
    else:
        for relative in AION177_PROHIBITED_SOURCE_FILES:
            if (repo_root / relative).exists():
                raise GovernanceValidationError(f"AION-178 runtime source must be absent: {relative}")


def validate_authorization_ledger(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "program_id mismatch")
    _require(payload.get("synthetic") is True, "authorization ledger must be synthetic")
    _require(payload.get("read_only") is True, "authorization ledger must be read_only")
    records = payload.get("records")
    _require(isinstance(records, list), "records must be a list")
    records = cast(list[dict[str, Any]], records)
    activation_stage = (
        payload.get("current_stage")
        == "shadow_activation_control_plane_authorized_not_implemented"
    )
    _require(
        len(records) == (8 if activation_stage else 7),
        "authorization ledger record count",
    )
    if activation_stage:
        active_authorizations = [
            record.get("authorization_transaction_id")
            for record in records
            if record.get("authorization_active") is True
        ]
        _require(
            active_authorizations == [SHADOW_ACTIVATION_AUTHORIZATION_ID],
            "AION-180 implementation authorization must be the sole active authorization",
        )

    root_closeout = records[0]
    _require(root_closeout.get("record_kind") == "authorization_closeout", "missing root closeout")
    _require(
        root_closeout.get("authorization_transaction_id") == ROOT_AUTHORIZATION_ID,
        "root closeout id",
    )
    _require(root_closeout.get("authorization_active") is False, "root must be inactive")
    _require(root_closeout.get("authorization_consumed") is True, "root must be consumed")
    _require(root_closeout.get("authorization_consumed_by_task") == "AION-164", "root task")
    _require(root_closeout.get("authorization_consumed_by_pr") == 75, "root PR")
    _require(root_closeout.get("authorization_expired") is True, "root expired")
    _require(root_closeout.get("authorization_reusable") is False, "root reusable")

    parent_closeout = records[1]
    _require(
        parent_closeout.get("record_kind") == "authorization_closeout",
        "missing parent closeout",
    )
    _require(
        parent_closeout.get("authorization_transaction_id") == PARENT_AUTHORIZATION_ID,
        "parent closeout id",
    )
    _require(parent_closeout.get("authorization_active") is False, "parent must be inactive")
    _require(parent_closeout.get("authorization_consumed") is True, "parent must be consumed")
    _require(parent_closeout.get("authorization_consumed_by_task") == "AION-166", "parent task")
    _require(parent_closeout.get("authorization_consumed_by_pr") == 77, "parent PR")
    _require(
        parent_closeout.get("authorization_consumed_by_feature_commits")
        == [AION_166_FEATURE_COMMIT],
        "parent feature commit",
    )
    _require(
        parent_closeout.get("authorization_consumed_by_merge_commit") == AION_166_MERGE_COMMIT,
        "parent merge commit",
    )
    _require(parent_closeout.get("authorization_expired") is True, "parent expired")
    _require(parent_closeout.get("authorization_reusable") is False, "parent reusable")

    evaluation_closeout = records[2]
    _require(
        evaluation_closeout.get("record_kind") == "authorization_closeout",
        "missing evaluation closeout",
    )
    _require(
        evaluation_closeout.get("authorization_transaction_id") == EVALUATION_AUTHORIZATION_ID,
        "evaluation closeout id",
    )
    _require(
        evaluation_closeout.get("authorization_active") is False,
        "evaluation must be inactive",
    )
    _require(
        evaluation_closeout.get("authorization_consumed") is True,
        "evaluation must be consumed",
    )
    _require(
        evaluation_closeout.get("authorization_consumed_by_task") == "AION-168",
        "evaluation task",
    )
    _require(evaluation_closeout.get("authorization_consumed_by_pr") == 79, "evaluation PR")
    _require(
        evaluation_closeout.get("authorization_consumed_by_feature_commits")
        == [AION_168_FEATURE_COMMIT],
        "evaluation feature commit",
    )
    _require(
        evaluation_closeout.get("authorization_consumed_by_merge_commit")
        == AION_168_MERGE_COMMIT,
        "evaluation merge commit",
    )
    _require(evaluation_closeout.get("authorization_expired") is True, "evaluation expired")
    _require(evaluation_closeout.get("authorization_reusable") is False, "evaluation reusable")

    experiment_closeout = records[3]
    _require(
        experiment_closeout.get("record_kind") == "authorization_closeout",
        "missing experiment closeout",
    )
    _require(
        experiment_closeout.get("authorization_transaction_id") == EXPERIMENT_AUTHORIZATION_ID,
        "experiment closeout id",
    )
    _require(
        experiment_closeout.get("authorization_active") is False,
        "experiment must be inactive",
    )
    _require(
        experiment_closeout.get("authorization_consumed") is True,
        "experiment must be consumed",
    )
    _require(
        experiment_closeout.get("authorization_consumed_by_task") == "AION-170",
        "experiment task",
    )
    _require(experiment_closeout.get("authorization_consumed_by_pr") == 81, "experiment PR")
    _require(
        tuple(experiment_closeout.get("authorization_consumed_by_feature_commits", ()))
        == AION_170_FEATURE_COMMITS,
        "experiment feature commit",
    )
    _require(
        experiment_closeout.get("authorization_consumed_by_merge_commit") == AION_170_MERGE_COMMIT,
        "experiment merge commit",
    )
    _require(experiment_closeout.get("authorization_expired") is True, "experiment expired")
    _require(experiment_closeout.get("authorization_reusable") is False, "experiment reusable")

    rewrite_closeout = records[4]
    _require(
        rewrite_closeout.get("record_kind") == "authorization_closeout",
        "missing rewrite closeout",
    )
    _require(
        rewrite_closeout.get("authorization_transaction_id") == AUTHORIZATION_ID,
        "rewrite closeout id",
    )
    _require(
        rewrite_closeout.get("authorization_active") is False,
        "rewrite must be inactive",
    )
    _require(
        rewrite_closeout.get("authorization_consumed") is True,
        "rewrite must be consumed",
    )
    _require(
        rewrite_closeout.get("authorization_consumed_by_task") == "AION-172",
        "rewrite task",
    )
    _require(rewrite_closeout.get("authorization_consumed_by_pr") == 83, "rewrite PR")
    _require(
        rewrite_closeout.get("authorization_consumed_by_feature_commits")
        == [AION_172_FEATURE_COMMIT],
        "rewrite feature commit",
    )
    _require(
        rewrite_closeout.get("authorization_consumed_by_merge_commit") == AION_172_MERGE_COMMIT,
        "rewrite merge commit",
    )
    _require(rewrite_closeout.get("authorization_expired") is True, "rewrite expired")
    _require(rewrite_closeout.get("authorization_reusable") is False, "rewrite reusable")

    canary_closeout = records[5]
    _require(canary_closeout.get("record_kind") == "authorization_closeout", "missing canary closeout")
    _require(
        canary_closeout.get("authorization_transaction_id") == CANARY_AUTHORIZATION_ID,
        "authorization id",
    )
    _require(canary_closeout.get("approval_record_id") == CANARY_AUTHORIZATION_ID, "approval id")
    _require(
        canary_closeout.get("parent_authorization_transaction_id") == AUTHORIZATION_ID,
        "parent id",
    )
    _require(canary_closeout.get("implementation_task") == "AION-174", "implementation task")
    _require(
        canary_closeout.get("authorization_scope") == "approval-bound-canary-rollback-and-adaptive-policy",
        "authorization scope",
    )
    _require(canary_closeout.get("authorization_active") is False, "authorization inactive")
    _require(canary_closeout.get("authorization_consumed") is True, "authorization consumed")
    _require(canary_closeout.get("authorization_consumed_by_task") == "AION-174", "canary task")
    _require(canary_closeout.get("authorization_consumed_by_pr") == 85, "canary PR")
    _require(
        canary_closeout.get("authorization_consumed_by_feature_commits") == [AION_174_FEATURE_COMMIT],
        "canary feature commit",
    )
    _require(
        canary_closeout.get("authorization_consumed_by_merge_commit") == AION_174_MERGE_COMMIT,
        "canary merge commit",
    )
    _require(canary_closeout.get("authorization_expired") is True, "authorization expired")
    _require(canary_closeout.get("authorization_reusable") is False, "authorization reusable")
    _require(
        canary_closeout.get("self_improvement_platform_state") == "implemented_disabled",
        "platform state",
    )
    for key in GOVERNANCE_FALSE_FLAGS:
        _require(canary_closeout.get(key) is False, f"{key} must be false")
    for key in GOVERNANCE_TRUE_FLAGS:
        _require(canary_closeout.get(key) is True, f"{key} must be true")
    _require(tuple(canary_closeout.get("protected_paths", [])) == PROTECTED_PATHS, "protected paths")
    _require(tuple(canary_closeout.get("risk_levels", [])) == RISK_LEVELS, "risk levels")
    _require(
        tuple(canary_closeout.get("change_budget_dimensions", [])) == CHANGE_BUDGET_DIMENSIONS,
        "change budget dimensions",
    )
    _require(
        tuple(canary_closeout.get("approval_binding_requirements", []))
        == CANARY_APPROVAL_BINDING_REQUIREMENTS,
        "approval binding requirements",
    )
    _require(
        tuple(canary_closeout.get("test_weakening_controls", [])) == TEST_WEAKENING_CONTROLS,
        "test weakening controls",
    )
    _require(
        tuple(canary_closeout.get("approved_scope", [])) == CANARY_APPROVED_SCOPE,
        "approved canary scope",
    )
    _require(
        tuple(canary_closeout.get("prohibited_scope", [])) == CANARY_PROHIBITED_SCOPE,
        "prohibited canary scope",
    )

    shadow = records[6]
    shadow_closed = (
        payload.get("current_stage") == "shadow_mode_operator_evaluation_passed_disabled"
        or activation_stage
    )
    _validate_shadow_authorization_record(shadow, closed=shadow_closed)

    if activation_stage:
        activation = records[7]
        _validate_shadow_activation_authorization_record(activation)
        _require(
            payload.get("active_self_improvement_implementation_authorization_count") == 1,
            "active authorization count",
        )
        _require(
            payload.get("active_self_improvement_implementation_authorization")
            == SHADOW_ACTIVATION_AUTHORIZATION_ID,
            "active authorization id",
        )
        _require(
            payload.get("active_implementation_task") == SHADOW_ACTIVATION_IMPLEMENTATION_TASK,
            "active implementation task",
        )
        _require(
            payload.get("formal_closeout_task") == SHADOW_ACTIVATION_CLOSEOUT_TASK,
            "closeout task",
        )
        _require(payload.get("new_implementation_authorization_created") is True, "new auth")
        _require(payload.get("shadow_mode_implemented") is True, "shadow implemented")
        _require(payload.get("shadow_mode_runtime_enabled") is False, "shadow runtime")
        _require(
            payload.get("shadow_activation_control_plane_authorized") is True,
            "activation control plane authorized",
        )
        _require(
            payload.get("shadow_activation_control_plane_implemented") is False,
            "activation control plane implemented",
        )
        _require(payload.get("shadow_activation_enabled") is False, "shadow activation")
    elif shadow_closed:
        _require(
            payload.get("active_self_improvement_implementation_authorization_count") == 0,
            "active authorization count",
        )
        _require(
            payload.get("active_self_improvement_implementation_authorization") == "none",
            "active authorization id",
        )
        _require(payload.get("active_implementation_task") == "none", "active implementation task")
        _require(payload.get("formal_closeout_task") == SHADOW_OPERATOR_EVALUATION_TASK, "closeout task")
    else:
        _require(
            payload.get("active_self_improvement_implementation_authorization_count") == 1,
            "active authorization count",
        )
        _require(
            payload.get("active_self_improvement_implementation_authorization")
            == SHADOW_AUTHORIZATION_ID,
            "active authorization id",
        )
        _require(
            payload.get("active_implementation_task") == SHADOW_IMPLEMENTATION_TASK,
            "active implementation task",
        )


def validate_program_ledger(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "program ledger id")
    _require(payload.get("synthetic") is True, "program ledger must be synthetic")
    _require(payload.get("read_only") is True, "program ledger must be read_only")
    records = payload.get("records")
    _require(isinstance(records, list), "program records must be a list")
    records = cast(list[dict[str, Any]], records)
    by_task = {record.get("task_id"): record for record in records}
    _require("AION-164" in by_task, "AION-164 record missing")
    _require("AION-165" in by_task, "AION-165 record missing")
    _require("AION-166" in by_task, "AION-166 record missing")
    _require("AION-167" in by_task, "AION-167 record missing")
    _require("AION-168" in by_task, "AION-168 record missing")
    _require("AION-169" in by_task, "AION-169 record missing")
    _require("AION-170" in by_task, "AION-170 record missing")
    _require("AION-171" in by_task, "AION-171 record missing")
    _require("AION-172" in by_task, "AION-172 record missing")
    _require("AION-173" in by_task, "AION-173 record missing")
    _require("AION-174" in by_task, "AION-174 record missing")
    _require("AION-175" in by_task, "AION-175 record missing")
    _require("AION-176" in by_task, "AION-176 record missing")
    _require("AION-177" in by_task, "AION-177 record missing")
    _require("AION-178" in by_task, "AION-178 record missing")
    _require("AION-179" in by_task, "AION-179 record missing")
    _require("AION-180" in by_task, "AION-180 record missing")
    shadow_operator_closed = by_task.get("AION-179")
    aion164 = by_task["AION-164"]
    _require(aion164.get("pull_requests") == [75], "AION-164 PR mismatch")
    _require(
        "8b2938a8995a9109b677f240d82da3b4bdc5d73c" in aion164.get("merge_commits", []),
        "AION-164 merge commit missing",
    )
    _require(aion164.get("ci_result") == "pass", "AION-164 CI result")
    _require(aion164.get("authorization_transaction") == ROOT_AUTHORIZATION_ID, "AION-164 auth")
    aion165 = by_task["AION-165"]
    _require(aion165.get("authorization_transaction") == PARENT_AUTHORIZATION_ID, "AION-165 auth")
    _require(aion165.get("next_task") == "AION-166", "AION-165 next task")
    _require(aion165.get("pull_requests") == [76], "AION-165 PR mismatch")
    _require(
        "a40ea4c9f76a969cac291c33f0c3ef94aa078d6b" in aion165.get("merge_commits", []),
        "AION-165 merge commit missing",
    )
    _require(
        aion165.get("authorization_state") == "consumed_by_AION-166_closed_by_AION-167",
        "AION-165 authorization state",
    )
    aion166 = by_task["AION-166"]
    _require(aion166.get("authorization_transaction") == PARENT_AUTHORIZATION_ID, "AION-166 auth")
    _require(aion166.get("pull_requests") == [77], "AION-166 PR mismatch")
    _require(aion166.get("feature_commits") == [AION_166_FEATURE_COMMIT], "AION-166 feature")
    _require(
        aion166.get("merge_commits") == [AION_166_MERGE_COMMIT],
        "AION-166 merge commit missing",
    )
    _require(aion166.get("ci_result") == "pass", "AION-166 CI result")
    _require(aion166.get("next_task") == "AION-167", "AION-166 next task")
    _require(
        aion166.get("runtime_state") == "governance_plane_implemented_no_self_rewrite_runtime",
        "AION-166 runtime state",
    )
    aion167 = by_task["AION-167"]
    _require(
        aion167.get("authorization_transaction") == EVALUATION_AUTHORIZATION_ID,
        "AION-167 auth",
    )
    _require(aion167.get("pull_requests") == [78], "AION-167 PR mismatch")
    _require(aion167.get("feature_commits") == [AION_167_FEATURE_COMMIT], "AION-167 feature")
    _require(
        aion167.get("merge_commits") == [AION_167_MERGE_COMMIT],
        "AION-167 merge commit missing",
    )
    _require(aion167.get("ci_result") == "pass", "AION-167 CI result")
    _require(aion167.get("next_task") == "AION-168", "AION-167 next task")
    _require(
        aion167.get("authorization_state") == "consumed_by_AION-168_closed_by_AION-169",
        "AION-167 authorization state",
    )
    _require(
        aion167.get("runtime_state") == "authorization_only_no_evaluation_runtime_implementation",
        "AION-167 runtime state",
    )
    aion168 = by_task["AION-168"]
    _require(
        aion168.get("authorization_transaction") == EVALUATION_AUTHORIZATION_ID,
        "AION-168 auth",
    )
    _require(aion168.get("pull_requests") == [79], "AION-168 PR mismatch")
    _require(aion168.get("feature_commits") == [AION_168_FEATURE_COMMIT], "AION-168 feature")
    _require(
        aion168.get("merge_commits") == [AION_168_MERGE_COMMIT],
        "AION-168 merge commit missing",
    )
    _require(aion168.get("ci_result") == "pass", "AION-168 CI result")
    _require(aion168.get("next_task") == "AION-169", "AION-168 next task")
    _require(
        aion168.get("authorization_state") == "consumed_by_AION-168_closed_by_AION-169",
        "AION-168 authorization state",
    )
    _require(
        aion168.get("runtime_state") == "evaluation_plane_implemented_no_source_mutation_or_pr_creation",
        "AION-168 runtime state",
    )
    aion169 = by_task["AION-169"]
    _require(
        aion169.get("authorization_transaction") == EXPERIMENT_AUTHORIZATION_ID,
        "AION-169 auth",
    )
    _require(aion169.get("pull_requests") == [80], "AION-169 PR mismatch")
    _require(aion169.get("feature_commits") == [AION_169_FEATURE_COMMIT], "AION-169 feature")
    _require(
        aion169.get("merge_commits") == [AION_169_MERGE_COMMIT],
        "AION-169 merge commit missing",
    )
    _require(aion169.get("ci_result") == "pass", "AION-169 CI result")
    _require(aion169.get("next_task") == "AION-170", "AION-169 next task")
    _require(
        aion169.get("authorization_state") == "consumed_by_AION-170_closed_by_AION-171",
        "AION-169 authorization state",
    )
    _require(
        aion169.get("runtime_state") == "authorization_only_no_experiment_engine_implementation",
        "AION-169 runtime state",
    )
    aion170 = by_task["AION-170"]
    _require(
        aion170.get("authorization_transaction") == EXPERIMENT_AUTHORIZATION_ID,
        "AION-170 auth",
    )
    _require(aion170.get("pull_requests") == [81], "AION-170 PR mismatch")
    _require(
        tuple(aion170.get("feature_commits", ())) == AION_170_FEATURE_COMMITS,
        "AION-170 feature",
    )
    _require(
        aion170.get("merge_commits") == [AION_170_MERGE_COMMIT],
        "AION-170 merge commit missing",
    )
    _require(aion170.get("ci_result") == "pass", "AION-170 CI result")
    _require(aion170.get("next_task") == "AION-171", "AION-170 next task")
    _require(
        aion170.get("authorization_state") == "consumed_by_AION-170_closed_by_AION-171",
        "AION-170 authorization state",
    )
    _require(
        aion170.get("runtime_state")
        == "experiment_engine_implemented_no_source_mutation_or_git_or_pr_runtime",
        "AION-170 runtime state",
    )
    aion171 = by_task["AION-171"]
    _require(aion171.get("authorization_transaction") == AUTHORIZATION_ID, "AION-171 auth")
    _require(aion171.get("pull_requests") == [82], "AION-171 PR mismatch")
    _require(aion171.get("feature_commits") == [AION_171_FEATURE_COMMIT], "AION-171 feature")
    _require(
        aion171.get("merge_commits") == [AION_171_MERGE_COMMIT],
        "AION-171 merge commit missing",
    )
    _require(aion171.get("ci_result") == "pass", "AION-171 CI result")
    _require(aion171.get("next_task") == "AION-172", "AION-171 next task")
    _require(
        aion171.get("authorization_state") == "consumed_by_AION-172_closed_by_AION-173",
        "AION-171 authorization state",
    )
    _require(
        aion171.get("runtime_state") == "authorization_only_no_rewrite_controller_implementation",
        "AION-171 runtime state",
    )

    aion172 = by_task["AION-172"]
    _require(aion172.get("authorization_transaction") == AUTHORIZATION_ID, "AION-172 auth")
    _require(aion172.get("pull_requests") == [83], "AION-172 PR mismatch")
    _require(aion172.get("feature_commits") == [AION_172_FEATURE_COMMIT], "AION-172 feature")
    _require(
        aion172.get("merge_commits") == [AION_172_MERGE_COMMIT],
        "AION-172 merge commit missing",
    )
    _require(aion172.get("ci_result") == "pass", "AION-172 CI result")
    _require(aion172.get("next_task") == "AION-173", "AION-172 next task")
    _require(
        aion172.get("authorization_state") == "consumed_by_AION-172_closed_by_AION-173",
        "AION-172 authorization state",
    )
    _require(
        aion172.get("runtime_state")
        == "rewrite_controller_implemented_disabled_approval_bound_no_production_github_calls",
        "AION-172 runtime state",
    )

    aion173 = by_task["AION-173"]
    _require(
        aion173.get("authorization_transaction") == CANARY_AUTHORIZATION_ID,
        "AION-173 auth",
    )
    _require(aion173.get("pull_requests") == [84], "AION-173 PR mismatch")
    _require(aion173.get("feature_commits") == [AION_173_FEATURE_COMMIT], "AION-173 feature")
    _require(
        aion173.get("merge_commits") == [AION_173_MERGE_COMMIT],
        "AION-173 merge commit missing",
    )
    _require(aion173.get("ci_result") == "pass", "AION-173 CI result")
    _require(aion173.get("next_task") == "AION-174", "AION-173 next task")
    _require(
        aion173.get("authorization_state") == "active_until_AION-174_merge",
        "AION-173 authorization state",
    )
    _require(
        aion173.get("runtime_state")
        == "authorization_only_no_canary_runtime_or_adaptive_learning_implementation",
        "AION-173 runtime state",
    )

    aion174 = by_task["AION-174"]
    _require(
        aion174.get("authorization_transaction") == CANARY_AUTHORIZATION_ID,
        "AION-174 auth",
    )
    _require(
        aion174.get("branch") == "phase/self-improvement-canary-and-adaptation",
        "AION-174 branch",
    )
    _require(aion174.get("pull_requests") == [85], "AION-174 PR mismatch")
    _require(aion174.get("feature_commits") == [AION_174_FEATURE_COMMIT], "AION-174 feature")
    _require(
        aion174.get("merge_commits") == [AION_174_MERGE_COMMIT],
        "AION-174 merge commit missing",
    )
    _require(aion174.get("ci_result") == "pass", "AION-174 CI result")
    _require(aion174.get("next_task") == "AION-175", "AION-174 next task")
    _require(
        aion174.get("authorization_state") == "consumed_by_AION-174_closed_by_AION-175",
        "AION-174 authorization state",
    )
    _require(
        aion174.get("runtime_state")
        == "canary_adaptation_plane_implemented_disabled_data_only_no_production_activation",
        "AION-174 runtime state",
    )

    aion175 = by_task["AION-175"]
    _require(
        aion175.get("branch") == "phase/self-improvement-final-closeout",
        "AION-175 branch",
    )
    _require(
        aion175.get("authorization_transaction") == CANARY_AUTHORIZATION_ID,
        "AION-175 auth",
    )
    _require(aion175.get("pull_requests") == [86], "AION-175 PR mismatch")
    _require(
        aion175.get("feature_commits") == [AION_175_FEATURE_COMMIT],
        "AION-175 feature commit",
    )
    _require(
        aion175.get("merge_commits") == [AION_175_MERGE_COMMIT],
        "AION-175 merge commit",
    )
    _require(aion175.get("ci_result") == "pass", "AION-175 CI result")
    _require(aion175.get("next_task") == "operator_evaluation", "AION-175 next task")
    _require(
        aion175.get("authorization_state")
        == "final_closeout_complete_no_new_implementation_authorization",
        "AION-175 authorization state",
    )
    _require(
        aion175.get("runtime_state") == "self_improvement_platform_implemented_disabled",
        "AION-175 runtime state",
    )
    _require(
        aion175.get("completion_timestamp") == AION_175_MERGED_AT,
        "AION-175 completion timestamp",
    )

    aion176 = by_task["AION-176"]
    _require(
        aion176.get("branch") == "phase/self-improvement-postmerge-evidence-reconciliation",
        "AION-176 branch",
    )
    _require(aion176.get("pull_requests") == [87], "AION-176 PR mismatch")
    _require(aion176.get("feature_commits") == [AION_176_FEATURE_COMMIT], "AION-176 feature")
    _require(aion176.get("merge_commits") == [AION_176_MERGE_COMMIT], "AION-176 merge")
    _require(aion176.get("ci_result") == "pass", "AION-176 CI result")
    _require(aion176.get("next_task") == "AION-OE-001", "AION-176 next task")
    _require(
        aion176.get("authorization_state") == "no_new_implementation_authorization",
        "AION-176 authorization state",
    )
    _require(aion176.get("runtime_state") == "operator_evaluation_ready", "AION-176 runtime")
    _require(
        aion176.get("completion_timestamp") == AION_176_MERGED_AT,
        "AION-176 completion timestamp",
    )

    aion177 = by_task["AION-177"]
    _require(
        aion177.get("branch") == "phase/self-improvement-shadow-mode-authorization",
        "AION-177 branch",
    )
    _require(aion177.get("feature_commits") == [AION_177_FEATURE_COMMIT], "AION-177 feature")
    _require(aion177.get("pull_requests") == [88], "AION-177 PR mismatch")
    _require(aion177.get("merge_commits") == [AION_177_MERGE_COMMIT], "AION-177 merge")
    _require(aion177.get("ci_result") == "pass", "AION-177 CI result")
    _require(aion177.get("authorization_transaction") == SHADOW_AUTHORIZATION_ID, "AION-177 auth")
    _require(aion177.get("next_task") == SHADOW_IMPLEMENTATION_TASK, "AION-177 next task")
    if shadow_operator_closed:
        _require(
            aion177.get("authorization_state") == "consumed_by_AION-178_closed_by_AION-179",
            "AION-177 authorization state",
        )
        _require(
            aion177.get("runtime_state") == "shadow_mode_authorization_consumed_runtime_disabled",
            "AION-177 runtime state",
        )
    else:
        _require(
            aion177.get("authorization_state") == "active_until_AION-179_closeout",
            "AION-177 authorization state",
        )
        _require(
            aion177.get("runtime_state") == "shadow_mode_authorized_not_implemented",
            "AION-177 runtime state",
        )
    _require(
        aion177.get("completion_timestamp") == AION_177_MERGED_AT,
        "AION-177 completion timestamp",
    )

    aion178 = by_task["AION-178"]
    _require(
        aion178.get("branch") == "phase/self-improvement-shadow-mode-plane",
        "AION-178 branch",
    )
    if shadow_operator_closed:
        _require(aion178.get("feature_commits") == [AION_178_FEATURE_COMMIT], "AION-178 feature")
        _require(aion178.get("pull_requests") == [89], "AION-178 PR mismatch")
        _require(aion178.get("merge_commits") == [AION_178_MERGE_COMMIT], "AION-178 merge")
        _require(aion178.get("ci_result") == "pass", "AION-178 CI result")
    else:
        _require(aion178.get("feature_commits") == [], "AION-178 feature commits pending")
        _require(aion178.get("pull_requests") == [], "AION-178 PR pending")
        _require(aion178.get("merge_commits") == [], "AION-178 merge pending")
        _require(aion178.get("ci_result") == "pending", "AION-178 CI pending")
    _require(aion178.get("authorization_transaction") == SHADOW_AUTHORIZATION_ID, "AION-178 auth")
    if shadow_operator_closed:
        _require(
            aion178.get("authorization_state") == "consumed_by_AION-178_closed_by_AION-179",
            "AION-178 authorization state",
        )
    else:
        _require(
            aion178.get("authorization_state")
            == "implementation_in_progress_formal_closeout_AION-179",
            "AION-178 authorization state",
        )
    _require(aion178.get("next_task") == "AION-179", "AION-178 next task")
    if shadow_operator_closed:
        _require(
            aion178.get("runtime_state")
            == "shadow_mode_implemented_operator_invoked_disabled_closed_by_AION-179",
            "AION-178 runtime state",
        )
        _require(aion178.get("completion_timestamp") == AION_178_MERGED_AT, "AION-178 timestamp")
        aion179 = by_task["AION-179"]
        _require(
            aion179.get("branch") == "phase/self-improvement-shadow-mode-evaluation-closeout",
            "AION-179 branch",
        )
        _require(aion179.get("authorization_transaction") == SHADOW_AUTHORIZATION_ID, "AION-179 auth")
        _require(
            aion179.get("authorization_state")
            == "consumed_by_AION-178_closed_by_AION-179",
            "AION-179 authorization state",
        )
        _require(
            aion179.get("runtime_state") == "shadow_mode_operator_evaluation_passed_runtime_disabled",
            "AION-179 runtime state",
        )
        _require(tuple(aion179.get("feature_commits", ())) == AION_179_FEATURE_COMMITS, "AION-179 feature")
        _require(aion179.get("pull_requests") == [90], "AION-179 PR")
        _require(aion179.get("merge_commits") == [AION_179_MERGE_COMMIT], "AION-179 merge")
        _require(aion179.get("ci_result") == "pass", "AION-179 CI")
        _require(aion179.get("next_task") == "AION-180", "AION-179 next task")
        _require(aion179.get("completion_timestamp") == AION_179_MERGED_AT, "AION-179 timestamp")
        aion180 = by_task["AION-180"]
        _require(
            aion180.get("branch") == "phase/self-improvement-shadow-activation-authorization",
            "AION-180 branch",
        )
        _require(
            aion180.get("authorization_transaction") == SHADOW_ACTIVATION_AUTHORIZATION_ID,
            "AION-180 auth",
        )
        _require(
            aion180.get("authorization_state")
            == "active_for_AION-181_formal_closeout_AION-182",
            "AION-180 authorization state",
        )
        _require(
            aion180.get("runtime_state") == "activation_control_plane_authorized_not_implemented",
            "AION-180 runtime state",
        )
        _require(aion180.get("feature_commits") == [], "AION-180 feature pending")
        _require(aion180.get("pull_requests") == [], "AION-180 PR pending")
        _require(aion180.get("merge_commits") == [], "AION-180 merge pending")
        _require(aion180.get("ci_result") == "pending", "AION-180 CI pending")
        _require(aion180.get("next_task") == SHADOW_ACTIVATION_IMPLEMENTATION_TASK, "AION-180 next")
        _require(aion180.get("completion_timestamp") is None, "AION-180 timestamp pending")
    else:
        _require(
            aion178.get("runtime_state") == "shadow_mode_implemented_operator_invoked_disabled",
            "AION-178 runtime state",
        )
        _require(aion178.get("completion_timestamp") is None, "AION-178 timestamp pending")


def validate_operator_evaluation_closeout(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "operator closeout program id")
    _require(payload.get("evaluation_id") == OPERATOR_EVALUATION_ID, "operator evaluation id")
    _require(payload.get("synthetic") is True, "operator closeout must be synthetic")
    _require(payload.get("read_only") is True, "operator closeout must be read_only")
    _require(payload.get("decision") == OPERATOR_EVALUATION_DECISION, "operator decision")
    _require(payload.get("base_commit") == AION_176_MERGE_COMMIT, "operator base commit")
    _require(payload.get("new_implementation_authorization_created") is False, "operator auth")
    _require(payload.get("runtime_activation_created") is False, "operator runtime activation")
    validations = payload.get("validations", {})
    _require(isinstance(validations, dict), "operator validations")
    for key in (
        "runtime_hold",
        "final_integrated_check",
        "docs",
        "domain_drift",
        "boundary",
        "repository_health",
        "immutable_tag",
    ):
        _require(validations.get(key) == "PASS", f"operator validation {key}")


def validate_shadow_authorization_example(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "shadow example program id")
    _validate_shadow_authorization_record(payload)


def validate_shadow_runtime_hold_example(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "shadow runtime hold program id")
    _require(payload.get("authorization_transaction_id") == SHADOW_AUTHORIZATION_ID, "hold auth id")
    _require(payload.get("shadow_mode_authorized") is True, "shadow authorized")
    if payload.get("shadow_mode_implemented") is True:
        _require(
            payload.get("shadow_mode_implementation_state")
            == "implemented_operator_invoked_disabled",
            "shadow implementation state",
        )
        for relative in AION178_ALLOWED_CREATE:
            _require(relative in payload.get("required_source_files_present", []), relative)
    else:
        for relative in AION177_PROHIBITED_SOURCE_FILES:
            _require(relative in payload.get("prohibited_source_files_absent", []), relative)
    for key in SHADOW_PROHIBITED_FLAGS:
        _require(payload.get(key) is False, f"runtime hold {key}")


def validate_shadow_operator_evaluation_report(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "shadow operator report program id")
    _require(
        payload.get("activation_phase_id") == SHADOW_ACTIVATION_PHASE_ID,
        "shadow operator report phase",
    )
    _require(payload.get("task_id") == SHADOW_OPERATOR_EVALUATION_TASK, "shadow operator task")
    _require(payload.get("implementation_task") == SHADOW_IMPLEMENTATION_TASK, "shadow implementation task")
    _require(
        payload.get("authorization_transaction_id") == SHADOW_AUTHORIZATION_ID,
        "shadow operator authorization",
    )
    _require(payload.get("evaluation_id") == SHADOW_OPERATOR_EVALUATION_ID, "shadow evaluation id")
    _require(payload.get("evaluation_base_commit") == AION_178_MERGE_COMMIT, "shadow base commit")
    _require(payload.get("evaluated_pr") == 89, "shadow evaluated PR")
    _require(payload.get("evaluated_feature_commit") == AION_178_FEATURE_COMMIT, "shadow feature")
    _require(payload.get("evaluated_merge_commit") == AION_178_MERGE_COMMIT, "shadow merge")
    _require(payload.get("evaluated_merge_timestamp") == AION_178_MERGED_AT, "shadow merged at")
    _require(payload.get("synthetic") is True, "shadow operator synthetic")
    _require(payload.get("read_only") is True, "shadow operator read_only")
    _require(payload.get("redacted") is True, "shadow operator redacted")
    _require(payload.get("operator_invoked") is True, "shadow operator invoked")
    _require(payload.get("decision") == SHADOW_OPERATOR_EVALUATION_DECISION, "shadow decision")
    _require(payload.get("scenario_count") == 14, "shadow scenario count")
    scenarios = payload.get("scenario_results")
    _require(isinstance(scenarios, list), "shadow scenario results")
    scenarios = cast(list[dict[str, Any]], scenarios)
    _require(
        tuple(item.get("scenario_id") for item in scenarios)
        == (
            "no-pattern",
            "repeated-retrieval-failure",
            "planning-failure",
            "evidence-grounding-failure",
            "policy-violation",
            "budget-violation",
            "missing-reference",
            "fingerprint-mismatch",
            "protected-input-rejection",
            "output-boundary",
            "deterministic-replay",
            "retention",
            "bounded-concurrency",
            "runtime-influence-boundary",
        ),
        "shadow scenario registry",
    )
    for scenario in scenarios:
        _require(scenario.get("passed") is True, f"shadow scenario {scenario.get('scenario_id')}")
    hard_gates = payload.get("hard_gates")
    _require(isinstance(hard_gates, dict), "shadow hard gates")
    for key, value in cast(dict[str, Any], hard_gates).items():
        _require(value is True, f"shadow hard gate {key}")
    for key in (
        "runtime_activation_created",
        "new_implementation_authorization_created",
        "shadow_plane_runtime_enabled",
        "source_modified",
        "git_mutated",
        "pull_request_created",
        "approval_created",
        "runtime_effect",
        "active_learning_promoted",
    ):
        _require(payload.get(key) is False, f"shadow operator {key}")
    _require(
        payload.get("repository_digest_before") == payload.get("repository_digest_after"),
        "shadow repo digest",
    )


def validate_shadow_activation_transition(current_state: str, next_state: str) -> TransitionDecision:
    if current_state in SHADOW_ACTIVATION_FORBIDDEN_STATES:
        return TransitionDecision(current_state, next_state, False, "forbidden current state")
    if next_state in SHADOW_ACTIVATION_FORBIDDEN_STATES:
        return TransitionDecision(current_state, next_state, False, "forbidden next state")
    if current_state not in SHADOW_ACTIVATION_ALLOWED_TRANSITIONS:
        return TransitionDecision(current_state, next_state, False, "unknown current state")
    if next_state not in SHADOW_ACTIVATION_STATES:
        return TransitionDecision(current_state, next_state, False, "unknown next state")
    if next_state not in SHADOW_ACTIVATION_ALLOWED_TRANSITIONS[current_state]:
        return TransitionDecision(current_state, next_state, False, "unknown lifecycle transition")
    return TransitionDecision(current_state, next_state, True, "allowed lifecycle transition")


def require_shadow_activation_transition(current_state: str, next_state: str) -> TransitionDecision:
    decision = validate_shadow_activation_transition(current_state, next_state)
    if not decision.allowed:
        raise GovernanceValidationError(decision.reason)
    return decision


def validate_shadow_activation_authorization_example(payload: dict[str, Any]) -> None:
    _validate_shadow_activation_authorization_record(payload)


def validate_shadow_activation_runtime_hold_example(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "activation hold program id")
    _require(
        payload.get("activation_program_id") == SHADOW_ACTIVATION_PROGRAM_ID,
        "activation hold program",
    )
    _require(
        payload.get("authorization_transaction_id") == SHADOW_ACTIVATION_AUTHORIZATION_ID,
        "activation hold auth id",
    )
    _require(payload.get("synthetic") is True, "activation hold synthetic")
    _require(payload.get("read_only") is True, "activation hold read_only")
    _require(payload.get("redacted") is True, "activation hold redacted")
    _require(
        payload.get("shadow_activation_control_plane_authorized") is True,
        "activation control plane authorized",
    )
    _require(
        payload.get("shadow_activation_control_plane_implemented") is False,
        "activation control plane implemented",
    )
    for key in (*GOVERNANCE_FALSE_FLAGS, *SHADOW_PROHIBITED_FLAGS, *SHADOW_ACTIVATION_PROHIBITED_FLAGS):
        if key in payload:
            _require(payload.get(key) is False, f"activation hold {key}")


def _validate_shadow_activation_authorization_record(record: dict[str, Any]) -> None:
    _require(record.get("record_kind") == "implementation_authorization", "activation record kind")
    _require(
        record.get("program_id") == PROGRAM_ID,
        "activation program id",
    )
    _require(
        record.get("activation_program_id") == SHADOW_ACTIVATION_PROGRAM_ID,
        "activation program",
    )
    _require(
        record.get("authorization_transaction_id") == SHADOW_ACTIVATION_AUTHORIZATION_ID,
        "activation authorization id",
    )
    _require(
        record.get("approval_record_id") == SHADOW_ACTIVATION_AUTHORIZATION_ID,
        "activation approval id",
    )
    _require(record.get("parent_evaluation_id") == SHADOW_OPERATOR_EVALUATION_ID, "parent evaluation")
    _require(record.get("parent_closeout_task") == SHADOW_OPERATOR_EVALUATION_TASK, "parent closeout")
    _require(record.get("parent_main_commit") == AION_179_MERGE_COMMIT, "parent main")
    _require(
        record.get("parent_shadow_implementation_commit") == AION_178_MERGE_COMMIT,
        "parent shadow implementation",
    )
    _require(
        record.get("parent_authorization_transaction_id") == SHADOW_AUTHORIZATION_ID,
        "parent authorization",
    )
    _require(
        record.get("candidate_id") == SHADOW_ACTIVATION_CANDIDATE_ID,
        "activation candidate",
    )
    _require(
        record.get("workstream") == SHADOW_ACTIVATION_WORKSTREAM,
        "activation workstream",
    )
    _require(
        record.get("implementation_task") == SHADOW_ACTIVATION_IMPLEMENTATION_TASK,
        "activation implementation task",
    )
    _require(
        record.get("formal_closeout_task") == SHADOW_ACTIVATION_CLOSEOUT_TASK,
        "activation closeout task",
    )
    _require(record.get("authorization_scope") == SHADOW_ACTIVATION_SCOPE, "activation scope")
    _require(record.get("authorization_active") is True, "activation active")
    _require(record.get("authorization_consumed") is False, "activation consumed")
    _require(record.get("authorization_expired") is False, "activation expired")
    _require(record.get("authorization_reusable") is False, "activation reusable")
    _require(record.get("shadow_mode_implemented") is True, "shadow implemented")
    _require(record.get("shadow_mode_runtime_enabled") is False, "shadow_mode_runtime_enabled")
    _require(
        record.get("shadow_activation_control_plane_authorized") is True,
        "activation control plane authorized",
    )
    _require(
        record.get("shadow_activation_control_plane_implemented") is False,
        "activation control plane implemented",
    )
    _require(record.get("shadow_activation_enabled") is False, "shadow_activation_enabled")
    _require(
        record.get("shadow_activation_actual_activation_authorized") is False,
        "actual activation authorized",
    )
    _require(
        record.get("future_activation_requires_separate_authorization") is True,
        "future activation separate authorization",
    )
    for key in SHADOW_ACTIVATION_APPROVED_FLAGS:
        _require(record.get(key) is True, f"{key} must be true")
    for key in (*GOVERNANCE_FALSE_FLAGS, *SHADOW_PROHIBITED_FLAGS, *SHADOW_ACTIVATION_PROHIBITED_FLAGS):
        if key in record:
            _require(record.get(key) is False, f"{key} must be false")
    allowed_approved_flags = set(SHADOW_ACTIVATION_APPROVED_FLAGS)
    for key, value in record.items():
        if (
            key.endswith("_approved") or key.endswith("_approval")
        ) and value is True and key not in allowed_approved_flags:
            raise GovernanceValidationError(f"extra approved capability: {key}")
    _require(
        tuple(record.get("allowed_aion181_create_paths", [])) == SHADOW_ACTIVATION_ALLOWED_CREATE,
        "activation create paths",
    )
    _require(
        tuple(record.get("allowed_aion181_update_paths", [])) == SHADOW_ACTIVATION_ALLOWED_UPDATE,
        "activation update paths",
    )
    _require(
        tuple(record.get("candidate_contract_required_fields", []))
        == SHADOW_ACTIVATION_REQUIRED_CANDIDATE_FIELDS,
        "activation candidate fields",
    )
    _require(
        tuple(record.get("request_contract_required_fields", []))
        == SHADOW_ACTIVATION_REQUIRED_REQUEST_FIELDS,
        "activation request fields",
    )
    _require(
        tuple(record.get("approval_binding_required_fields", []))
        == SHADOW_ACTIVATION_APPROVAL_BINDING_FIELDS,
        "activation approval binding fields",
    )
    _require(
        tuple(record.get("shadow_activation_allowed_outcomes", []))
        == SHADOW_ACTIVATION_ALLOWED_OUTCOMES,
        "activation allowed outcomes",
    )
    _require(record.get("shadow_activation_forbidden_outcomes") == ["active"], "active outcome")
    _require(tuple(record.get("shadow_activation_states", [])) == SHADOW_ACTIVATION_STATES, "states")
    _require(
        tuple(record.get("shadow_activation_forbidden_states", []))
        == SHADOW_ACTIVATION_FORBIDDEN_STATES,
        "forbidden states",
    )
    transitions = record.get("shadow_activation_allowed_transitions")
    _require(isinstance(transitions, dict), "activation transitions")
    for state, allowed in SHADOW_ACTIVATION_ALLOWED_TRANSITIONS.items():
        _require(set(transitions.get(state, [])) == allowed, f"transition {state}")
    _require(record.get("resource_limits") == SHADOW_ACTIVATION_RESOURCE_LIMITS, "resource limits")
    _require(
        tuple(record.get("monitored_values", [])) == SHADOW_ACTIVATION_MONITORED_VALUES,
        "monitored values",
    )
    _require(
        tuple(record.get("deactivation_triggers", [])) == SHADOW_ACTIVATION_DEACTIVATION_TRIGGERS,
        "deactivation triggers",
    )
    _require(
        tuple(record.get("threats_addressed", [])) == SHADOW_ACTIVATION_THREATS,
        "activation threats",
    )


def _validate_shadow_authorization_record(record: dict[str, Any], *, closed: bool = False) -> None:
    expected_kind = "authorization_closeout" if closed else "implementation_authorization"
    _require(record.get("record_kind") == expected_kind, "shadow record kind")
    _require(
        record.get("authorization_transaction_id") == SHADOW_AUTHORIZATION_ID,
        "shadow authorization id",
    )
    _require(record.get("approval_record_id") == SHADOW_AUTHORIZATION_ID, "shadow approval id")
    _require(record.get("program_id") == PROGRAM_ID, "shadow program id")
    _require(record.get("activation_phase_id") == SHADOW_ACTIVATION_PHASE_ID, "shadow phase id")
    _require(record.get("candidate_id") == SHADOW_CANDIDATE_ID, "shadow candidate")
    _require(record.get("workstream") == SHADOW_WORKSTREAM, "shadow workstream")
    _require(record.get("implementation_task") == SHADOW_IMPLEMENTATION_TASK, "shadow task")
    _require(record.get("authorization_scope") == SHADOW_AUTHORIZATION_SCOPE, "shadow scope")
    if closed:
        _require(record.get("authorization_active") is False, "shadow active")
        _require(record.get("authorization_consumed") is True, "shadow consumed")
        _require(record.get("authorization_consumed_by_task") == SHADOW_IMPLEMENTATION_TASK, "shadow task")
        _require(record.get("authorization_consumed_by_pr") == 89, "shadow PR")
        _require(
            record.get("authorization_consumed_by_feature_commits") == [AION_178_FEATURE_COMMIT],
            "shadow feature commit",
        )
        _require(
            record.get("authorization_consumed_by_merge_commit") == AION_178_MERGE_COMMIT,
            "shadow merge commit",
        )
        _require(record.get("authorization_consumed_at") == AION_178_MERGED_AT, "shadow consumed at")
        _require(record.get("authorization_expired") is True, "shadow expired")
        _require(
            record.get("formal_closeout_task") == SHADOW_OPERATOR_EVALUATION_TASK,
            "shadow formal closeout task",
        )
        _require(
            record.get("closeout_evaluation_id") == SHADOW_OPERATOR_EVALUATION_ID,
            "shadow closeout evaluation",
        )
        _require(
            record.get("shadow_operator_evaluation_decision") == SHADOW_OPERATOR_EVALUATION_DECISION,
            "shadow operator evaluation decision",
        )
        _require(
            record.get("new_implementation_authorization_created") is False,
            "shadow closeout new authorization",
        )
        _require(record.get("runtime_activation_created") is False, "shadow runtime activation")
    else:
        _require(record.get("authorization_active") is True, "shadow active")
        _require(record.get("authorization_consumed") is False, "shadow consumed")
        _require(record.get("authorization_expired") is False, "shadow expired")
    _require(record.get("authorization_reusable") is False, "shadow reusable")
    _require(record.get("parent_evaluation_id") == OPERATOR_EVALUATION_ID, "parent evaluation id")
    _require(record.get("parent_closeout_task") == "AION-176", "parent closeout task")
    _require(record.get("parent_main_commit") == AION_176_MERGE_COMMIT, "parent main commit")
    _require(record.get("operator_evaluation_decision") == OPERATOR_EVALUATION_DECISION, "decision")
    _require(record.get("operator_evaluation_used_as_approval") is False, "operator approval")
    _require(record.get("operator_evaluation_reusable") is False, "operator reusable")
    _require(record.get("shadow_mode_authorized") is True, "shadow authorized")
    if record.get("shadow_mode_implemented") is True:
        _require(
            record.get("shadow_mode_implementation_state")
            == "implemented_operator_invoked_disabled",
            "shadow implementation state",
        )
        _require(
            record.get("operator_invoked_shadow_runs_supported") is True,
            "operator-invoked shadow runs supported",
        )
        _require(
            record.get("operator_invoked_batch_runner_available") is True,
            "operator batch runner available",
        )
    else:
        _require(record.get("shadow_mode_implemented") is False, "shadow implemented")
    _require(
        record.get("shadow_mode_runtime_enabled") is False,
        "shadow_mode_runtime_enabled must be false",
    )
    _require(record.get("self_improvement_platform_state") == "implemented_disabled", "platform")
    for key in GOVERNANCE_FALSE_FLAGS:
        _require(record.get(key) is False, f"{key} must be false")
    for key in SHADOW_APPROVED_FLAGS:
        _require(record.get(key) is True, f"{key} must be true")
    for key in SHADOW_PROHIBITED_FLAGS:
        _require(record.get(key) is False, f"{key} must be false")
    allowed_approved_flags = set(SHADOW_APPROVED_FLAGS)
    for key, value in record.items():
        if (
            key.endswith("_approved") or key.endswith("_approval")
        ) and value is True and key not in allowed_approved_flags:
            raise GovernanceValidationError(f"extra approved capability: {key}")
    _require(tuple(record.get("approved_scope", [])) == SHADOW_APPROVED_SCOPE, "shadow approved")
    _require(
        tuple(record.get("prohibited_scope", [])) == SHADOW_PROHIBITED_SCOPE,
        "shadow prohibited",
    )
    _require(tuple(record.get("allowed_inputs", [])) == SHADOW_ALLOWED_INPUTS, "allowed inputs")
    _require(
        tuple(record.get("disallowed_inputs", [])) == SHADOW_DISALLOWED_INPUTS,
        "disallowed inputs",
    )
    _require(
        tuple(record.get("allowed_outputs", [])) == SHADOW_ALLOWED_OUTPUT_FLAGS,
        "allowed outputs",
    )
    _require(
        tuple(record.get("allowed_review_states", [])) == SHADOW_ALLOWED_REVIEW_STATES,
        "allowed review states",
    )
    _require(
        tuple(record.get("forbidden_review_states", [])) == SHADOW_FORBIDDEN_REVIEW_STATES,
        "forbidden review states",
    )
    _require(record.get("resource_budgets") == SHADOW_RESOURCE_BUDGETS, "resource budgets")


def _current_authorization_record(payload: dict[str, Any]) -> dict[str, Any]:
    records = cast(list[dict[str, Any]], payload.get("records", []))
    matches = [
        record for record in records if record.get("authorization_active") is True
    ]
    if matches:
        _require(len(matches) == 1, "at most one active self-improvement authorization required")
        if matches[0].get("authorization_transaction_id") == SHADOW_ACTIVATION_AUTHORIZATION_ID:
            _validate_shadow_activation_authorization_record(matches[0])
            return matches[0]
        _require(matches[0].get("authorization_transaction_id") == SHADOW_AUTHORIZATION_ID, "active authorization")
        return matches[0]
    if payload.get("current_stage") == "shadow_mode_operator_evaluation_passed_disabled":
        closed_matches = [
            record
            for record in records
            if record.get("authorization_transaction_id") == SHADOW_AUTHORIZATION_ID
        ]
        _require(len(closed_matches) == 1, "one closed AION-177 shadow-mode authorization required")
        _validate_shadow_authorization_record(closed_matches[0], closed=True)
        return closed_matches[0]
    raise GovernanceValidationError("one active AION-177 shadow-mode authorization required")


def _require_required_docs(repo_root: Path) -> None:
    required = (
        *REQUIRED_DOCS,
        *AION177_REQUIRED_DOCS,
        *AION177_REQUIRED_EXAMPLES,
        *AION178_REQUIRED_DOCS,
        *AION178_REQUIRED_EXAMPLES,
        *AION179_REQUIRED_DOCS,
        *AION179_REQUIRED_EXAMPLES,
        *AION180_REQUIRED_DOCS,
        *AION180_REQUIRED_EXAMPLES,
    )
    for relative in required:
        if not (repo_root / relative).is_file():
            raise GovernanceValidationError(f"missing required doc: {relative}")


def _validate_adr_index(repo_root: Path) -> None:
    index = (repo_root / "docs/adr/README.md").read_text()
    if "0156-governed-self-improvement-control-plane.md" not in index:
        raise GovernanceValidationError("ADR 0156 is not indexed")
    if "0157-self-improvement-evaluation-authorization.md" not in index:
        raise GovernanceValidationError("ADR 0157 is not indexed")
    if "0158-self-improvement-experiment-authorization.md" not in index:
        raise GovernanceValidationError("ADR 0158 is not indexed")
    if "0159-self-improvement-rewrite-authorization.md" not in index:
        raise GovernanceValidationError("ADR 0159 is not indexed")
    if "0160-self-improvement-canary-authorization.md" not in index:
        raise GovernanceValidationError("ADR 0160 is not indexed")
    if "0161-governed-self-improvement-platform-complete.md" not in index:
        raise GovernanceValidationError("ADR 0161 is not indexed")
    if "0162-controlled-self-improvement-shadow-mode-authorization.md" not in index:
        raise GovernanceValidationError("ADR 0162 is not indexed")
    if "0163-controlled-self-improvement-shadow-mode-plane.md" not in index:
        raise GovernanceValidationError("ADR 0163 is not indexed")
    if "0164-controlled-shadow-mode-operator-evaluation.md" not in index:
        raise GovernanceValidationError("ADR 0164 is not indexed")
    if "0165-controlled-shadow-activation-control-plane-authorization.md" not in index:
        raise GovernanceValidationError("ADR 0165 is not indexed")


def _validate_docs_do_not_store_private_material(repo_root: Path) -> None:
    for relative in REQUIRED_DOCS:
        path = repo_root / relative
        if relative == "docs/self-improvement/authorization-ledger.json":
            payload = _load_json(path)
            text = json.dumps(_redact_formal_no_go_labels(payload)).lower()
        else:
            text = path.read_text().lower()
        for marker in PRIVATE_MARKERS:
            if marker in text:
                raise GovernanceValidationError(f"private marker found in {relative}: {marker}")


def _redact_formal_no_go_labels(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if key in SHADOW_PROHIBITED_FLAGS or key in SHADOW_ACTIVATION_PROHIBITED_FLAGS or key in {
                "disallowed_inputs",
                "prohibited_scope",
                "prohibited_additions_for_AION_178",
            }:
                continue
            redacted[key] = _redact_formal_no_go_labels(item)
        return redacted
    if isinstance(value, list):
        return [_redact_formal_no_go_labels(item) for item in value]
    return value


def _load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise GovernanceValidationError(f"{path} must contain a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernanceValidationError(message)


def validate_shadow_operator_evaluation_no_go(repo_root: Path) -> None:
    validate_repo(repo_root)
    validate_no_go(repo_root)


def validate_shadow_operator_evaluation(repo_root: Path) -> None:
    validate_shadow_operator_evaluation_no_go(repo_root)


def validate_shadow_activation_authorization_no_go(repo_root: Path) -> None:
    validate_repo(repo_root)
    validate_no_go(repo_root)


def validate_shadow_activation_authorization(repo_root: Path) -> None:
    validate_shadow_activation_authorization_no_go(repo_root)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--mode",
        choices=(
            "check",
            "no-go",
            "shadow-operator-evaluation-no-go",
            "shadow-operator-evaluation",
            "shadow-activation-authorization-no-go",
            "shadow-activation-authorization",
        ),
        default="check",
    )
    args = parser.parse_args()

    if args.mode == "check":
        validate_repo(args.repo_root)
        validate_sequence(
            (
                "observed",
                "hypothesized",
                "test_created",
                "experiment_ready",
                "patch_created",
                "sandbox_running",
                "sandbox_passed",
                "approval_pending",
                "approved",
                "pr_created",
                "merged",
                "canary",
                "promoted",
                "archived",
            )
        )
    elif args.mode == "no-go":
        validate_repo(args.repo_root)
        validate_no_go(args.repo_root)
    elif args.mode == "shadow-operator-evaluation-no-go":
        validate_shadow_operator_evaluation_no_go(args.repo_root)
    elif args.mode == "shadow-operator-evaluation":
        validate_shadow_operator_evaluation(args.repo_root)
    elif args.mode == "shadow-activation-authorization-no-go":
        validate_shadow_activation_authorization_no_go(args.repo_root)
    else:
        validate_shadow_activation_authorization(args.repo_root)
    print(f"self-improvement governance {args.mode} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
