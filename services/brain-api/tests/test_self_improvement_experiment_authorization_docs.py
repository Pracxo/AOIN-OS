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
    AUTHORIZATION_ID,
    EXPERIMENT_APPROVED_SCOPE,
    EXPERIMENT_PROHIBITED_SCOPE,
    GOVERNANCE_FALSE_FLAGS,
    GOVERNANCE_TRUE_FLAGS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion169_authorizes_only_proposal_and_experiment_engine() -> None:
    payload = _authorization()
    validate_authorization_ledger(payload)
    active = payload["records"][3]

    assert active["authorization_transaction_id"] == AUTHORIZATION_ID
    assert active["parent_authorization_transaction_id"] == "AION-167-SI-0002"
    assert active["implementation_task"] == "AION-170"
    assert active["authorization_scope"] == "self-improvement-proposal-and-experiment-engine"
    assert tuple(active["approved_scope"]) == EXPERIMENT_APPROVED_SCOPE
    assert tuple(active["prohibited_scope"]) == EXPERIMENT_PROHIBITED_SCOPE
    for key in GOVERNANCE_FALSE_FLAGS:
        assert active[key] is False
    for key in GOVERNANCE_TRUE_FLAGS:
        assert active[key] is True


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
        payload["records"][3][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion169_requires_experiment_scope_and_no_direct_promotion() -> None:
    payload = _authorization()
    active = payload["records"][3]

    assert "failure-pattern intake" in active["approved_scope"]
    assert "baseline/candidate experiment execution" in active["approved_scope"]
    assert "approval-pending lifecycle" in active["approved_scope"]
    assert "Git commits" in active["prohibited_scope"]
    assert "pull request creation" in active["prohibited_scope"]
    assert "merge" in active["prohibited_scope"]

    active["approved_scope"] = [
        item for item in active["approved_scope"] if item != "regression-test proposals"
    ]
    with pytest.raises(GovernanceValidationError, match="approved experiment scope"):
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


def _nested_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AION_AGGREGATE_GATE_RUNNING"] = "1"
    return env
