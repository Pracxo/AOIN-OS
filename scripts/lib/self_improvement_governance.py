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

REQUIRED_DOCS = (
    "docs/self-improvement/governance-charter.md",
    "docs/self-improvement/evaluation-authorization.md",
    "docs/self-improvement/experiment-authorization.md",
    "docs/self-improvement/rewrite-authorization.md",
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
    _validate_docs_do_not_store_private_material(repo_root)


def validate_no_go(repo_root: Path) -> None:
    authorization = _load_json(repo_root / "docs/self-improvement/authorization-ledger.json")
    active = _active_authorization(authorization)
    for key in GOVERNANCE_FALSE_FLAGS:
        if active.get(key) is not False:
            raise GovernanceValidationError(f"{key} must be false")
    for key in GOVERNANCE_TRUE_FLAGS:
        if active.get(key) is not True:
            raise GovernanceValidationError(f"{key} must be true")
    required_prohibited_scope = (
        REWRITE_PROHIBITED_SCOPE
        if active.get("authorization_transaction_id") == AUTHORIZATION_ID
        else EXPERIMENT_PROHIBITED_SCOPE
    )
    for item in required_prohibited_scope:
        if item not in active.get("prohibited_scope", []):
            raise GovernanceValidationError(f"{item} must be prohibited")


def validate_authorization_ledger(payload: dict[str, Any]) -> None:
    _require(payload.get("program_id") == PROGRAM_ID, "program_id mismatch")
    _require(payload.get("synthetic") is True, "authorization ledger must be synthetic")
    _require(payload.get("read_only") is True, "authorization ledger must be read_only")
    records = payload.get("records")
    _require(isinstance(records, list), "records must be a list")
    records = cast(list[dict[str, Any]], records)
    _require(len(records) == 5, "AION-171 authorization ledger must have five records")

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

    active = records[4]
    _require(active.get("record_kind") == "authorization_transaction", "missing active record")
    _require(active.get("authorization_transaction_id") == AUTHORIZATION_ID, "authorization id")
    _require(active.get("approval_record_id") == AUTHORIZATION_ID, "approval id")
    _require(
        active.get("parent_authorization_transaction_id") == EXPERIMENT_AUTHORIZATION_ID,
        "parent id",
    )
    _require(active.get("implementation_task") == "AION-172", "implementation task")
    _require(
        active.get("authorization_scope") == "approval-bound-isolated-source-rewrite-and-pr-control",
        "authorization scope",
    )
    _require(active.get("authorization_active") is True, "authorization active")
    _require(active.get("authorization_consumed") is False, "authorization consumed")
    _require(active.get("authorization_expired") is False, "authorization expired")
    _require(active.get("authorization_reusable") is False, "authorization reusable")
    for key in GOVERNANCE_FALSE_FLAGS:
        _require(active.get(key) is False, f"{key} must be false")
    for key in GOVERNANCE_TRUE_FLAGS:
        _require(active.get(key) is True, f"{key} must be true")
    _require(tuple(active.get("protected_paths", [])) == PROTECTED_PATHS, "protected paths")
    _require(tuple(active.get("risk_levels", [])) == RISK_LEVELS, "risk levels")
    _require(
        tuple(active.get("change_budget_dimensions", [])) == CHANGE_BUDGET_DIMENSIONS,
        "change budget dimensions",
    )
    _require(
        tuple(active.get("approval_binding_requirements", [])) == APPROVAL_BINDING_REQUIREMENTS,
        "approval binding requirements",
    )
    _require(
        tuple(active.get("test_weakening_controls", [])) == TEST_WEAKENING_CONTROLS,
        "test weakening controls",
    )
    _require(
        tuple(active.get("approved_scope", [])) == REWRITE_APPROVED_SCOPE,
        "approved rewrite scope",
    )
    _require(
        tuple(active.get("prohibited_scope", [])) == REWRITE_PROHIBITED_SCOPE,
        "prohibited rewrite scope",
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
    _require(aion171.get("next_task") == "AION-172", "AION-171 next task")
    _require(
        aion171.get("authorization_state") == "active_until_AION-172_merge",
        "AION-171 authorization state",
    )
    _require(
        aion171.get("runtime_state") == "authorization_only_no_rewrite_controller_implementation",
        "AION-171 runtime state",
    )


def _active_authorization(payload: dict[str, Any]) -> dict[str, Any]:
    matches = [
        record for record in payload.get("records", []) if record.get("authorization_active") is True
    ]
    _require(len(matches) == 1, "exactly one active self-improvement authorization required")
    return matches[0]


def _require_required_docs(repo_root: Path) -> None:
    for relative in REQUIRED_DOCS:
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


def _validate_docs_do_not_store_private_material(repo_root: Path) -> None:
    for relative in REQUIRED_DOCS:
        text = (repo_root / relative).read_text().lower()
        for marker in PRIVATE_MARKERS:
            if marker in text:
                raise GovernanceValidationError(f"private marker found in {relative}: {marker}")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise GovernanceValidationError(f"{path} must contain a JSON object")
    return payload


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernanceValidationError(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--mode", choices=("check", "no-go"), default="check")
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
    else:
        validate_repo(args.repo_root)
        validate_no_go(args.repo_root)
    print(f"self-improvement governance {args.mode} PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
