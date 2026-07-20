"""AION-182 shadow activation operator evaluation harness tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "scripts" / "lib"

if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from self_improvement_shadow_activation_operator_evaluation import (  # noqa: E402
    EXPECTED_EVALUATION_BASE_COMMIT,
    FAIL_DECISION,
    PASS_DECISION,
    REQUIRED_HARD_GATES,
    SCENARIO_IDS,
    EvaluationFailure,
    build_report,
    validate_operator_evaluation_report,
)


def test_shadow_activation_operator_evaluation_harness_records_pass(tmp_path: Path) -> None:
    report = build_report(
        repo_root=ROOT,
        evaluation_id="AION-SACE-001",
        evaluation_base_commit=EXPECTED_EVALUATION_BASE_COMMIT,
        temporary_output_directory=tmp_path,
    )

    assert report["decision"] == PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 21
    assert tuple(item["scenario_id"] for item in report["scenario_results"]) == SCENARIO_IDS
    assert all(item["passed"] for item in report["scenario_results"])
    assert set(report["hard_gate_results"]) == set(REQUIRED_HARD_GATES)
    assert all(report["hard_gate_results"].values())
    assert report["repository_digest_before"] == report["repository_digest_after"]
    assert report["repository_integrity"]["canonical_repository_untouched_by_evaluation"] is True
    assert report["repository_integrity"]["control_plane_git_operation_count"] == 0
    assert report["repository_integrity"]["control_plane_source_mutation_count"] == 0
    assert report["repository_integrity"]["control_plane_real_pull_request_created"] is False
    assert report["new_implementation_authorization_created"] is False
    assert report["activation_approval_created"] is False
    assert report["actual_activation_created"] is False
    assert report["shadow_activation_enabled"] is False
    assert report["runtime_effect"] is False


def test_shadow_activation_operator_evaluation_harness_fails_closed_for_wrong_base(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="evaluation base commit"):
        build_report(
            repo_root=ROOT,
            evaluation_id="AION-SACE-001",
            evaluation_base_commit="0" * 40,
            temporary_output_directory=tmp_path,
        )


def test_shadow_activation_operator_evaluation_import_boundary() -> None:
    text = (HARNESS_DIR / "self_improvement_shadow_activation_operator_evaluation.py").read_text()
    forbidden = (
        "import subprocess",
        "import socket",
        "import requests",
        "import httpx",
        "import aiohttp",
        "import git",
        "import github",
        "worktree",
        "patch_generator",
        "git_controller",
        "pr_controller",
        "merge_controller",
        "self_improvement.canary",
        "rollback_controller",
    )

    for marker in forbidden:
        assert marker not in text
    assert "InMemoryShadowActivationEvidenceAdapter" in text
    assert "ExplicitLocalShadowEvidenceBundleAdapter" in text
    assert "ControlledShadowActivationSimulator" in text


def test_shadow_activation_operator_evaluation_report_validation_rejects_bad_shapes(
    tmp_path: Path,
) -> None:
    report = build_report(
        repo_root=ROOT,
        evaluation_id="AION-SACE-001",
        evaluation_base_commit=EXPECTED_EVALUATION_BASE_COMMIT,
        temporary_output_directory=tmp_path,
    )

    unknown = {**report, "decision": "UNKNOWN"}
    with pytest.raises(EvaluationFailure, match="unknown evaluation decision"):
        validate_operator_evaluation_report(unknown)

    duplicate = {
        **report,
        "scenario_results": [*report["scenario_results"], report["scenario_results"][0]],
    }
    with pytest.raises(EvaluationFailure, match="duplicate scenario"):
        validate_operator_evaluation_report(duplicate)

    missing_gate = {**report, "hard_gate_results": dict(report["hard_gate_results"])}
    missing_gate["hard_gate_results"].pop("no_runtime_effect_occurred")
    with pytest.raises(EvaluationFailure, match="missing hard gate"):
        validate_operator_evaluation_report(missing_gate)

    false_gate = {**report, "hard_gate_results": dict(report["hard_gate_results"])}
    false_gate["hard_gate_results"]["no_runtime_effect_occurred"] = False
    with pytest.raises(EvaluationFailure, match="PASS cannot"):
        validate_operator_evaluation_report(false_gate)

    fail = {**report, "decision": FAIL_DECISION, "evaluation_passed": True}
    with pytest.raises(EvaluationFailure, match="FAIL cannot"):
        validate_operator_evaluation_report(fail)
