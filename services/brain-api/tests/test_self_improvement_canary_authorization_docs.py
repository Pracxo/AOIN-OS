"""AION-173 self-improvement canary authorization tests."""

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
    AUTHORIZATION_ID,
    CANARY_APPROVAL_BINDING_REQUIREMENTS,
    CANARY_APPROVED_SCOPE,
    CANARY_AUTHORIZATION_ID,
    CANARY_PROHIBITED_SCOPE,
    GOVERNANCE_FALSE_FLAGS,
    GOVERNANCE_TRUE_FLAGS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion173_closes_rewrite_authorization_and_authorizes_canary_plane() -> None:
    payload = _authorization()
    validate_authorization_ledger(payload)
    rewrite_closeout = payload["records"][4]
    active = payload["records"][5]

    assert rewrite_closeout["authorization_transaction_id"] == AUTHORIZATION_ID
    assert rewrite_closeout["authorization_active"] is False
    assert rewrite_closeout["authorization_consumed"] is True
    assert rewrite_closeout["authorization_consumed_by_task"] == "AION-172"
    assert rewrite_closeout["authorization_consumed_by_pr"] == 83
    assert rewrite_closeout["authorization_consumed_by_feature_commits"] == [
        AION_172_FEATURE_COMMIT
    ]
    assert rewrite_closeout["authorization_consumed_by_merge_commit"] == AION_172_MERGE_COMMIT
    assert rewrite_closeout["authorization_reusable"] is False

    assert active["authorization_transaction_id"] == CANARY_AUTHORIZATION_ID
    assert active["approval_record_id"] == CANARY_AUTHORIZATION_ID
    assert active["parent_authorization_transaction_id"] == AUTHORIZATION_ID
    assert active["implementation_task"] == "AION-174"
    assert active["authorization_scope"] == "approval-bound-canary-rollback-and-adaptive-policy"
    assert tuple(active["approved_scope"]) == CANARY_APPROVED_SCOPE
    assert tuple(active["prohibited_scope"]) == CANARY_PROHIBITED_SCOPE
    assert tuple(active["approval_binding_requirements"]) == CANARY_APPROVAL_BINDING_REQUIREMENTS
    for key in GOVERNANCE_FALSE_FLAGS:
        assert active[key] is False
    for key in GOVERNANCE_TRUE_FLAGS:
        assert active[key] is True


def test_aion173_blocks_canary_activation_policy_relaxation_and_self_approval() -> None:
    validate_no_go(ROOT)
    for flag in [
        "production_canary_enabled",
        "unrestricted_traffic_exposure_enabled",
        "automatic_protected_core_modification_enabled",
        "automatic_policy_relaxation_enabled",
        "runtime_self_approval_enabled",
        "autonomous_production_activation_enabled",
        "model_weight_training_enabled",
        "model_weight_changes_enabled",
    ]:
        payload = _authorization()
        payload["records"][5][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion173_requires_exact_canary_and_adaptive_policy_binding() -> None:
    payload = _authorization()
    active = payload["records"][5]

    assert "exact merge commit" in active["approval_binding_requirements"]
    assert "exact deployment artifact" in active["approval_binding_requirements"]
    assert "exact exposure budget" in active["approval_binding_requirements"]
    assert "exact monitoring duration" in active["approval_binding_requirements"]
    assert "exact metric thresholds" in active["approval_binding_requirements"]
    assert "exact adaptive policy version" in active["approval_binding_requirements"]

    active["approval_binding_requirements"] = [
        item
        for item in active["approval_binding_requirements"]
        if item != "exact exposure budget"
    ]
    with pytest.raises(GovernanceValidationError, match="approval binding requirements"):
        validate_authorization_ledger(payload)


def test_aion173_prohibits_unrestricted_exposure_and_autonomous_activation() -> None:
    payload = _authorization()
    active = payload["records"][5]

    assert "production canary by default" in active["prohibited_scope"]
    assert "unrestricted traffic exposure" in active["prohibited_scope"]
    assert "automatic policy relaxation" in active["prohibited_scope"]
    assert "runtime self-approval" in active["prohibited_scope"]
    assert "autonomous production activation" in active["prohibited_scope"]

    active["prohibited_scope"] = [
        item for item in active["prohibited_scope"] if item != "runtime self-approval"
    ]
    with pytest.raises(GovernanceValidationError, match="prohibited canary scope"):
        validate_authorization_ledger(payload)


def test_aion173_scripts_are_executable_and_pass_in_nested_gate_context() -> None:
    scripts = [
        "scripts/self-improvement-canary-no-go-regression.sh",
        "scripts/self-improvement-canary-authorization-check.sh",
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
