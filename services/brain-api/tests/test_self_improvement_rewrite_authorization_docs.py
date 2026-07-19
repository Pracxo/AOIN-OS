"""AION-171 self-improvement rewrite authorization tests."""

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
    AION_172_FEATURE_COMMIT,
    AION_172_MERGE_COMMIT,
    APPROVAL_BINDING_REQUIREMENTS,
    AUTHORIZATION_ID,
    EXPERIMENT_AUTHORIZATION_ID,
    REWRITE_APPROVED_SCOPE,
    REWRITE_PROHIBITED_SCOPE,
    TEST_WEAKENING_CONTROLS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion171_authorizes_only_approval_bound_rewrite_controller() -> None:
    payload = _authorization()
    validate_authorization_ledger(payload)
    closeout = payload["records"][4]
    historical = _text("docs/self-improvement/rewrite-authorization.md")

    assert closeout["authorization_transaction_id"] == AUTHORIZATION_ID
    assert closeout["authorization_active"] is False
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_consumed_by_task"] == "AION-172"
    assert closeout["authorization_consumed_by_pr"] == 83
    assert closeout["authorization_consumed_by_feature_commits"] == [AION_172_FEATURE_COMMIT]
    assert closeout["authorization_consumed_by_merge_commit"] == AION_172_MERGE_COMMIT
    assert closeout["authorization_reusable"] is False

    assert AUTHORIZATION_ID in historical
    assert EXPERIMENT_AUTHORIZATION_ID in historical
    for item in REWRITE_APPROVED_SCOPE:
        assert item in historical
    for item in REWRITE_PROHIBITED_SCOPE:
        assert item in historical
    for item in APPROVAL_BINDING_REQUIREMENTS:
        assert item in historical
    for item in TEST_WEAKENING_CONTROLS:
        assert item in historical


def test_aion171_blocks_runtime_rewrite_merge_deploy_and_self_approval() -> None:
    validate_no_go(ROOT)
    for flag in [
        "self_rewrite_runtime_enabled",
        "source_rewriting_enabled",
        "source_mutation_enabled",
        "git_commits_enabled",
        "branch_creation_enabled",
        "pull_request_creation_enabled",
        "merge_enabled",
        "automatic_merge_enabled",
        "automatic_approval_enabled",
        "deployment_enabled",
        "production_deployment_enabled",
        "model_weight_changes_enabled",
        "model_weight_training_enabled",
    ]:
        payload = _authorization()
        payload["records"][5][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion171_requires_exact_approval_binding_and_test_integrity_controls() -> None:
    payload = _authorization()
    historical = _text("docs/self-improvement/rewrite-authorization.md")

    assert "exact commit SHA" in historical
    assert "exact diff hash" in historical
    assert "exact benchmark fingerprint" in historical
    assert "exact rollback commit" in historical
    assert "detect deleted assertions" in historical
    assert "detect skipped tests" in historical
    assert "detect changed benchmark thresholds" in historical

    payload["records"][4]["authorization_consumed_by_feature_commits"] = []
    with pytest.raises(GovernanceValidationError, match="rewrite feature commit"):
        validate_authorization_ledger(payload)


def test_aion171_prohibits_direct_main_force_push_and_unapproved_merge() -> None:
    payload = _authorization()
    historical = _text("docs/self-improvement/rewrite-authorization.md")

    assert "direct main writes" in historical
    assert "force pushes" in historical
    assert "self-approval" in historical
    assert "automatic merge without approval" in historical
    assert "production deployment" in historical

    payload["records"][4]["authorization_consumed_by_merge_commit"] = "deadbeef"
    with pytest.raises(GovernanceValidationError, match="rewrite merge commit"):
        validate_authorization_ledger(payload)


def test_aion171_scripts_are_executable_and_pass_in_nested_gate_context() -> None:
    scripts = [
        "scripts/self-improvement-rewrite-no-go-regression.sh",
        "scripts/self-improvement-rewrite-authorization-check.sh",
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
