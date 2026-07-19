"""AION-169 self-improvement experiment authorization tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION_170_FEATURE_COMMITS,
    AION_170_MERGE_COMMIT,
    EXPERIMENT_AUTHORIZATION_ID,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion169_is_closed_after_proposal_and_experiment_engine_merge() -> None:
    payload = _authorization()
    validate_authorization_ledger(payload)
    closeout = payload["records"][3]

    assert closeout["authorization_transaction_id"] == EXPERIMENT_AUTHORIZATION_ID
    assert closeout["authorization_active"] is False
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_consumed_by_task"] == "AION-170"
    assert closeout["authorization_consumed_by_pr"] == 81
    assert closeout["authorization_consumed_by_feature_commits"] == list(
        AION_170_FEATURE_COMMITS
    )
    assert closeout["authorization_consumed_by_merge_commit"] == AION_170_MERGE_COMMIT
    assert closeout["authorization_reusable"] is False


def test_aion169_blocks_source_git_pr_merge_deploy_and_model_changes() -> None:
    validate_no_go(ROOT)
    for flag in [
        "source_mutation_enabled",
        "source_rewriting_enabled",
        "git_commits_enabled",
        "branch_creation_enabled",
        "pull_request_creation_enabled",
        "merge_enabled",
        "deployment_enabled",
        "production_deployment_enabled",
        "model_weight_changes_enabled",
        "model_weight_training_enabled",
    ]:
        payload = _authorization()
        payload["records"][5][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion169_requires_experiment_scope_and_no_direct_promotion() -> None:
    payload = _authorization()
    historical = _text("docs/self-improvement/experiment-authorization.md")

    assert "failure-pattern intake" in historical
    assert "baseline/candidate experiment execution" in historical
    assert "approval-pending lifecycle" in historical
    assert "Git commits" in historical
    assert "pull request creation" in historical
    assert "merge" in historical

    payload["records"][3]["authorization_consumed_by_feature_commits"] = []
    with pytest.raises(GovernanceValidationError, match="experiment feature commit"):
        validate_authorization_ledger(payload)


def test_aion169_scripts_are_executable_and_pass_in_nested_gate_context() -> None:
    scripts = [
        "scripts/self-improvement-experiment-no-go-regression.sh",
        "scripts/self-improvement-experiment-authorization-check.sh",
    ]
    for relative in scripts:
        mode = (ROOT / relative).stat().st_mode
        assert mode & stat.S_IXUSR, relative
        subprocess.run([str(ROOT / relative)], cwd=ROOT, check=True, env=_nested_env())


def _authorization() -> dict[str, Any]:
    with (ROOT / "docs/self-improvement/authorization-ledger.json").open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _nested_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AION_AGGREGATE_GATE_RUNNING"] = "1"
    return env
