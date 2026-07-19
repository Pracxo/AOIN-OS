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
    APPROVAL_BINDING_REQUIREMENTS,
    AUTHORIZATION_ID,
    EXPERIMENT_AUTHORIZATION_ID,
    GOVERNANCE_FALSE_FLAGS,
    GOVERNANCE_TRUE_FLAGS,
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
    active = payload["records"][4]

    assert active["authorization_transaction_id"] == AUTHORIZATION_ID
    assert active["parent_authorization_transaction_id"] == EXPERIMENT_AUTHORIZATION_ID
    assert active["implementation_task"] == "AION-172"
    assert active["authorization_scope"] == "approval-bound-isolated-source-rewrite-and-pr-control"
    assert tuple(active["approved_scope"]) == REWRITE_APPROVED_SCOPE
    assert tuple(active["prohibited_scope"]) == REWRITE_PROHIBITED_SCOPE
    assert tuple(active["approval_binding_requirements"]) == APPROVAL_BINDING_REQUIREMENTS
    assert tuple(active["test_weakening_controls"]) == TEST_WEAKENING_CONTROLS
    for key in GOVERNANCE_FALSE_FLAGS:
        assert active[key] is False
    for key in GOVERNANCE_TRUE_FLAGS:
        assert active[key] is True


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
        payload["records"][4][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion171_requires_exact_approval_binding_and_test_integrity_controls() -> None:
    payload = _authorization()
    active = payload["records"][4]

    assert "exact commit SHA" in active["approval_binding_requirements"]
    assert "exact diff hash" in active["approval_binding_requirements"]
    assert "exact benchmark fingerprint" in active["approval_binding_requirements"]
    assert "exact rollback commit" in active["approval_binding_requirements"]
    assert "detect deleted assertions" in active["test_weakening_controls"]
    assert "detect skipped tests" in active["test_weakening_controls"]
    assert "detect changed benchmark thresholds" in active["test_weakening_controls"]

    active["approval_binding_requirements"] = [
        item for item in active["approval_binding_requirements"] if item != "exact diff hash"
    ]
    with pytest.raises(GovernanceValidationError, match="approval binding requirements"):
        validate_authorization_ledger(payload)


def test_aion171_prohibits_direct_main_force_push_and_unapproved_merge() -> None:
    payload = _authorization()
    active = payload["records"][4]

    assert "direct main writes" in active["prohibited_scope"]
    assert "force pushes" in active["prohibited_scope"]
    assert "self-approval" in active["prohibited_scope"]
    assert "automatic merge without approval" in active["prohibited_scope"]
    assert "production deployment" in active["prohibited_scope"]

    active["prohibited_scope"] = [
        item for item in active["prohibited_scope"] if item != "self-approval"
    ]
    with pytest.raises(GovernanceValidationError, match="prohibited rewrite scope"):
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


def _nested_env() -> dict[str, str]:
    env = os.environ.copy()
    env["AION_AGGREGATE_GATE_RUNNING"] = "1"
    return env
