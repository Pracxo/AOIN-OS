"""AION-175 final closeout and user-evaluation readiness tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from aion_brain.self_improvement import (
    CANARY_RUNTIME_ENABLED,
    PRODUCTION_EXPOSURE_ENABLED,
    DisabledCIMonitorAdapter,
    DisabledGitCommandRunner,
    DisabledMergeAdapter,
    DisabledPatchGenerator,
    DisabledPullRequestAdapter,
    DisabledSandboxRunner,
    MergeRequest,
    PatchRequest,
    PullRequestCreateRequest,
    SandboxCommand,
)

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION_174_FEATURE_COMMIT,
    AION_174_MERGE_COMMIT,
    AION_175_FEATURE_COMMIT,
    AION_175_MERGE_COMMIT,
    AION_175_MERGED_AT,
    AION_178_FEATURE_COMMIT,
    AION_178_MERGE_COMMIT,
    AION_178_MERGED_AT,
    AION_181_FEATURE_COMMIT,
    AION_181_MERGE_COMMIT,
    CANARY_AUTHORIZATION_ID,
    GOVERNANCE_FALSE_FLAGS,
    GOVERNANCE_TRUE_FLAGS,
    SHADOW_ACTIVATION_AUTHORIZATION_ID,
    SHADOW_ACTIVATION_OPERATOR_EVALUATION_ID,
    SHADOW_ACTIVATION_OPERATOR_EVALUATION_PASS_DECISION,
    SHADOW_AUTHORIZATION_ID,
    SHADOW_IMPLEMENTATION_TASK,
    SHADOW_OPERATOR_EVALUATION_DECISION,
    SHADOW_OPERATOR_EVALUATION_ID,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
    validate_program_ledger,
    validate_repo,
)

FINAL_DOCS = (
    "docs/self-improvement/final-architecture.md",
    "docs/self-improvement/operator-evaluation-guide.md",
    "docs/self-improvement/security-review.md",
    "docs/self-improvement/benchmark-report.md",
    "docs/self-improvement/end-to-end-evidence.md",
    "docs/self-improvement/known-limitations.md",
    "docs/self-improvement/runtime-activation-checklist.md",
    "docs/self-improvement/future-model-training-boundary.md",
    "docs/adr/0161-governed-self-improvement-platform-complete.md",
    "examples/self-improvement/final-readiness-report.json",
)

FINAL_TRUE_FLAGS = {
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
    "human_approval_required",
    "exact_commit_approval_required",
    "exact_diff_hash_approval_required",
    "no_self_approval",
    "protected_core_dual_approval_required",
    "holdout_protected",
    "rollback_required",
}

FINAL_RUNTIME_FALSE_FLAGS = {
    "self_improvement_runtime_enabled",
    "self_rewrite_runtime_enabled",
    "automatic_merge_enabled",
    "production_canary_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
}


def test_aion175_required_docs_reports_and_adr_index_are_present() -> None:
    validate_repo(ROOT)
    for relative in FINAL_DOCS:
        assert (ROOT / relative).is_file(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0161-governed-self-improvement-platform-complete.md" in adr_index
    canary_closeout = _text("docs/self-improvement/canary-authorization.md")
    assert "AION-175 closes `AION-173-SI-0005`" in canary_closeout
    assert "`authorization_active=false` after AION-175 closeout" in canary_closeout


def test_aion175_closes_canary_authorization_without_new_implementation_auth() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(payload)
    validate_no_go(ROOT)

    records = payload["records"]
    assert len(records) == 8
    active_records = [record for record in records if record["authorization_active"] is True]
    assert active_records == []
    assert payload["active_self_improvement_implementation_authorization_count"] == 0
    assert payload["active_self_improvement_implementation_authorization"] == "none"
    assert payload["active_implementation_task"] == "none"

    closeout = records[5]
    assert closeout["record_kind"] == "authorization_closeout"
    assert closeout["task_id"] == "AION-175"
    assert closeout["authorization_transaction_id"] == CANARY_AUTHORIZATION_ID
    assert closeout["approval_record_id"] == CANARY_AUTHORIZATION_ID
    assert closeout["implementation_task"] == "AION-174"
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_consumed_by_task"] == "AION-174"
    assert closeout["authorization_consumed_by_pr"] == 85
    assert closeout["authorization_consumed_by_feature_commits"] == [AION_174_FEATURE_COMMIT]
    assert closeout["authorization_consumed_by_merge_commit"] == AION_174_MERGE_COMMIT
    assert closeout["authorization_expired"] is True
    assert closeout["authorization_reusable"] is False
    assert closeout["self_improvement_platform_state"] == "implemented_disabled"
    for key in GOVERNANCE_FALSE_FLAGS:
        assert closeout[key] is False
    for key in GOVERNANCE_TRUE_FLAGS:
        assert closeout[key] is True
    for key in FINAL_TRUE_FLAGS:
        assert closeout[key] is True

    shadow_closeout = records[6]
    assert shadow_closeout["record_kind"] == "authorization_closeout"
    assert shadow_closeout["authorization_transaction_id"] == SHADOW_AUTHORIZATION_ID
    assert shadow_closeout["authorization_active"] is False
    assert shadow_closeout["authorization_consumed"] is True
    assert shadow_closeout["authorization_consumed_by_task"] == SHADOW_IMPLEMENTATION_TASK
    assert shadow_closeout["authorization_consumed_by_pr"] == 89
    assert shadow_closeout["authorization_consumed_by_feature_commits"] == [
        AION_178_FEATURE_COMMIT
    ]
    assert shadow_closeout["authorization_consumed_by_merge_commit"] == AION_178_MERGE_COMMIT
    assert shadow_closeout["authorization_consumed_at"] == AION_178_MERGED_AT
    assert shadow_closeout["authorization_expired"] is True
    assert shadow_closeout["authorization_reusable"] is False
    assert shadow_closeout["closeout_evaluation_id"] == SHADOW_OPERATOR_EVALUATION_ID
    assert (
        shadow_closeout["shadow_operator_evaluation_decision"]
        == SHADOW_OPERATOR_EVALUATION_DECISION
    )
    assert shadow_closeout["new_implementation_authorization_created"] is False
    assert shadow_closeout["runtime_activation_created"] is False

    activation_closeout = records[7]
    assert activation_closeout["record_kind"] == "authorization_closeout"
    assert activation_closeout["authorization_transaction_id"] == SHADOW_ACTIVATION_AUTHORIZATION_ID
    assert activation_closeout["authorization_active"] is False
    assert activation_closeout["authorization_consumed"] is True
    assert activation_closeout["authorization_consumed_by_task"] == "AION-181"
    assert activation_closeout["authorization_consumed_by_pr"] == 92
    assert activation_closeout["authorization_consumed_by_feature_commits"] == [
        AION_181_FEATURE_COMMIT
    ]
    assert activation_closeout["authorization_consumed_by_merge_commit"] == AION_181_MERGE_COMMIT
    assert activation_closeout["authorization_expired"] is True
    assert activation_closeout["authorization_reusable"] is False
    assert (
        activation_closeout["control_plane_operator_evaluation_id"]
        == SHADOW_ACTIVATION_OPERATOR_EVALUATION_ID
    )
    assert (
        activation_closeout["control_plane_operator_evaluation_decision"]
        == SHADOW_ACTIVATION_OPERATOR_EVALUATION_PASS_DECISION
    )
    assert activation_closeout["control_plane_operator_evaluation_used_as_approval"] is False
    assert (
        activation_closeout["control_plane_operator_evaluation_created_implementation_authorization"]
        is False
    )
    assert (
        activation_closeout["control_plane_operator_evaluation_created_activation_approval"]
        is False
    )
    assert (
        activation_closeout["control_plane_operator_evaluation_created_actual_activation"]
        is False
    )

    mutated = _json("docs/self-improvement/authorization-ledger.json")
    mutated["records"][5]["self_improvement_runtime_enabled"] = True
    with pytest.raises(GovernanceValidationError, match="self_improvement_runtime_enabled"):
        validate_authorization_ledger(mutated)


def test_aion175_program_ledger_records_merged_final_task() -> None:
    payload = _json("docs/self-improvement/program-ledger.json")
    validate_program_ledger(payload)
    by_task = {record["task_id"]: record for record in payload["records"]}

    assert by_task["AION-174"]["pull_requests"] == [85]
    assert by_task["AION-174"]["feature_commits"] == [AION_174_FEATURE_COMMIT]
    assert by_task["AION-174"]["merge_commits"] == [AION_174_MERGE_COMMIT]
    assert by_task["AION-174"]["authorization_state"] == (
        "consumed_by_AION-174_closed_by_AION-175"
    )

    closeout = by_task["AION-175"]
    assert closeout["branch"] == "phase/self-improvement-final-closeout"
    assert closeout["authorization_transaction"] == CANARY_AUTHORIZATION_ID
    assert (
        closeout["authorization_state"]
        == "final_closeout_complete_no_new_implementation_authorization"
    )
    assert closeout["runtime_state"] == "self_improvement_platform_implemented_disabled"
    assert closeout["next_task"] == "operator_evaluation"
    assert closeout["pull_requests"] == [86]
    assert closeout["feature_commits"] == [AION_175_FEATURE_COMMIT]
    assert closeout["merge_commits"] == [AION_175_MERGE_COMMIT]
    assert closeout["ci_result"] == "pass"
    assert closeout["completion_timestamp"] == AION_175_MERGED_AT

    aion177 = by_task["AION-177"]
    assert aion177["authorization_transaction"] == SHADOW_AUTHORIZATION_ID
    assert aion177["authorization_state"] == "consumed_by_AION-178_closed_by_AION-179"
    assert aion177["next_task"] == SHADOW_IMPLEMENTATION_TASK
    assert aion177["runtime_state"] == "shadow_mode_authorization_consumed_runtime_disabled"

    aion178 = by_task["AION-178"]
    assert aion178["authorization_transaction"] == SHADOW_AUTHORIZATION_ID
    assert aion178["authorization_state"] == "consumed_by_AION-178_closed_by_AION-179"
    assert (
        aion178["runtime_state"]
        == "shadow_mode_implemented_operator_invoked_disabled_closed_by_AION-179"
    )
    assert aion178["next_task"] == "AION-179"
    assert aion178["pull_requests"] == [89]
    assert aion178["feature_commits"] == [AION_178_FEATURE_COMMIT]
    assert aion178["merge_commits"] == [AION_178_MERGE_COMMIT]
    assert aion178["ci_result"] == "pass"
    assert aion178["completion_timestamp"] == AION_178_MERGED_AT

    aion179 = by_task["AION-179"]
    assert aion179["authorization_transaction"] == SHADOW_AUTHORIZATION_ID
    assert aion179["authorization_state"] == "consumed_by_AION-178_closed_by_AION-179"
    assert aion179["runtime_state"] == "shadow_mode_operator_evaluation_passed_runtime_disabled"
    assert aion179["next_task"] == "AION-180"
    assert aion179["ci_result"] == "pass"


def test_final_readiness_report_has_required_capabilities_safety_and_evaluation_steps() -> None:
    report = _json("examples/self-improvement/final-readiness-report.json")
    runtime_state = report["runtime_state"]
    approval_state = report["approval_state"]
    security_gates = report["security_gates"]

    assert report["program_id"] == "AION-SELF-IMPROVEMENT-001"
    assert report["task_id"] == "AION-175"
    assert report["synthetic"] is True
    assert report["read_only"] is True
    assert report["report_state"] == "final_closeout_merged_evidence"
    assert report["current_stage"] == "operator_evaluation"
    assert runtime_state["self_improvement_platform_implemented"] is True
    assert runtime_state["self_improvement_platform_state"] == "implemented_disabled"
    for key in FINAL_TRUE_FLAGS:
        if key in runtime_state:
            assert runtime_state[key] is True
    for key in FINAL_RUNTIME_FALSE_FLAGS:
        assert runtime_state[key] is False
    assert approval_state["authorization_active"] is False
    assert approval_state["authorization_consumed"] is True
    assert approval_state["new_implementation_authorization_created"] is False
    assert approval_state["human_approval_required"] is True
    assert approval_state["exact_commit_approval_required"] is True
    assert approval_state["exact_diff_hash_approval_required"] is True
    assert approval_state["no_self_approval"] is True

    false_safety = {
        "direct_main_writes",
        "self_approval",
        "automatic_merge",
        "production_deployment",
        "production_canary",
        "protected_core_ordinary_modification",
        "benchmark_self_modification",
        "holdout_disclosure",
        "test_weakening_allowed",
        "runtime_self_rewrite",
        "model_weight_training",
        "v02_tag_created",
        "v02_release_created",
    }
    for key in false_safety:
        assert security_gates[key] is False
    assert security_gates["aion_v010_unchanged"] is True
    assert "operator evaluation" in report["remaining_blockers"]
    assert "run ./scripts/self-improvement-runtime-hold.sh" in report["user_evaluation_steps"]
    assert any(component == "outcome ledger" for component in report["architecture_components"])


def test_runtime_hold_blocks_autonomous_runtime_activation_paths() -> None:
    assert CANARY_RUNTIME_ENABLED is False
    assert PRODUCTION_EXPOSURE_ENABLED is False

    patch_request = PatchRequest(
        proposal_id="proposal-175-test",
        base_sha="a" * 40,
        allowed_paths=("services/brain-api/tests/test_self_improvement_final_closeout_docs.py",),
        regression_test_path="services/brain-api/tests/test_self_improvement_final_closeout_docs.py",
        target_paths=("services/brain-api/tests/test_self_improvement_final_closeout_docs.py",),
    )
    pr_request = PullRequestCreateRequest(
        proposal_id="proposal-175-test",
        branch_name="phase/self-improvement-final-closeout",
        head_sha="b" * 40,
        diff_hash="c" * 64,
        title="AION-175 synthetic disabled PR request",
        body="Synthetic request used only to verify disabled runtime defaults.",
    )
    merge_request = MergeRequest(
        proposal_id="proposal-175-test",
        pr_number=175,
        head_sha="b" * 40,
        approved_commit_sha="b" * 40,
        benchmark_fingerprint="d" * 64,
        approved_benchmark_fingerprint="d" * 64,
    )
    sandbox_command = SandboxCommand(gate_name="focused_tests", command=("pytest", "-q"))

    with pytest.raises(RuntimeError, match="patch generation is disabled"):
        DisabledPatchGenerator().generate(patch_request)
    with pytest.raises(RuntimeError, match="sandbox execution is disabled"):
        DisabledSandboxRunner().run(sandbox_command)
    with pytest.raises(RuntimeError, match="pull request creation is disabled"):
        DisabledPullRequestAdapter().create_pull_request(pr_request)
    with pytest.raises(RuntimeError, match="pull request merge is disabled"):
        DisabledMergeAdapter().merge_pull_request(merge_request)
    with pytest.raises(RuntimeError, match="CI monitoring is disabled"):
        DisabledCIMonitorAdapter().checks_for_pull_request(175, "b" * 40)
    with pytest.raises(RuntimeError, match="local Git command execution is disabled"):
        DisabledGitCommandRunner().run_git(ROOT, ("status", "--short"))


def test_aion175_scripts_are_executable_and_pass_in_nested_gate_context() -> None:
    scripts = [
        "scripts/self-improvement-runtime-hold.sh",
        "scripts/self-improvement-final-check.sh",
    ]
    for relative in scripts:
        mode = (ROOT / relative).stat().st_mode
        assert mode & stat.S_IXUSR, relative
        subprocess.run([str(ROOT / relative)], cwd=ROOT, check=True, env=_nested_env())


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _nested_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AION_AGGREGATE_GATE_RUNNING"] = "1"
    return env
