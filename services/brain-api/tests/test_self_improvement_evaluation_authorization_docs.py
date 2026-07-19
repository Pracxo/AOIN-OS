"""AION-167 immutable evaluation authorization tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AUTHORIZATION_ID,
    CANARY_APPROVED_SCOPE,
    CANARY_AUTHORIZATION_ID,
    CANARY_PROHIBITED_SCOPE,
    EVALUATION_APPROVED_SCOPE,
    EVALUATION_AUTHORIZATION_ID,
    EVALUATION_PROHIBITED_SCOPE,
    EXPERIMENT_AUTHORIZATION_ID,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion167_is_closed_after_immutable_evaluation_plane_merge() -> None:
    payload = _authorization()
    validate_authorization_ledger(payload)
    evaluation_closeout = payload["records"][2]
    experiment_closeout = payload["records"][3]
    rewrite_closeout = payload["records"][4]
    active = payload["records"][5]

    assert evaluation_closeout["authorization_transaction_id"] == EVALUATION_AUTHORIZATION_ID
    assert evaluation_closeout["authorization_consumed_by_task"] == "AION-168"
    assert evaluation_closeout["authorization_consumed_by_pr"] == 79
    assert evaluation_closeout["authorization_active"] is False
    assert evaluation_closeout["authorization_reusable"] is False

    assert experiment_closeout["authorization_transaction_id"] == EXPERIMENT_AUTHORIZATION_ID
    assert experiment_closeout["authorization_consumed_by_task"] == "AION-170"
    assert experiment_closeout["authorization_active"] is False

    assert rewrite_closeout["authorization_transaction_id"] == AUTHORIZATION_ID
    assert rewrite_closeout["authorization_consumed_by_task"] == "AION-172"
    assert rewrite_closeout["authorization_active"] is False

    assert active["authorization_transaction_id"] == CANARY_AUTHORIZATION_ID
    assert active["implementation_task"] == "AION-174"
    assert tuple(active["approved_scope"]) == CANARY_APPROVED_SCOPE
    assert tuple(active["prohibited_scope"]) == CANARY_PROHIBITED_SCOPE


def test_aion169_continues_to_block_rewrite_pr_approval_deploy_and_training_flags() -> None:
    validate_no_go(ROOT)
    prohibited_flags = [
        "source_mutation_enabled",
        "source_rewriting_enabled",
        "git_commits_enabled",
        "branch_creation_enabled",
        "pull_request_creation_enabled",
        "merge_enabled",
        "automatic_approval_enabled",
        "production_deployment_enabled",
        "deployment_enabled",
        "model_weight_training_enabled",
        "model_weight_changes_enabled",
    ]
    for flag in prohibited_flags:
        payload = _authorization()
        payload["records"][5][flag] = True
        with pytest.raises(GovernanceValidationError, match=flag):
            validate_authorization_ledger(payload)


def test_aion167_scope_remains_recorded_as_consumed_evaluation_authorization() -> None:
    payload = _authorization()
    consumed_scope = set(EVALUATION_APPROVED_SCOPE)
    consumed_prohibitions = set(EVALUATION_PROHIBITED_SCOPE)

    assert "benchmark contracts" in consumed_scope
    assert "benchmark mutation through candidate code" in consumed_prohibitions
    assert payload["records"][2]["authorization_consumed_by_feature_commits"] == [
        "8d1402f6c122098f3aec5809cf94539992b45d10"
    ]

    payload["records"][2]["authorization_consumed_by_pr"] = 80
    with pytest.raises(GovernanceValidationError, match="evaluation PR"):
        validate_authorization_ledger(payload)


def _authorization() -> dict[str, Any]:
    with (ROOT / "docs/self-improvement/authorization-ledger.json").open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
