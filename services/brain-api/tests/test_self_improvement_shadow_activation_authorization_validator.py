"""AION-180 shadow activation authorization validator tests."""

from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    SHADOW_ACTIVATION_APPROVED_FLAGS,
    SHADOW_ACTIVATION_AUTHORIZATION_ID,
    SHADOW_ACTIVATION_PROHIBITED_FLAGS,
    SHADOW_AUTHORIZATION_ID,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
)


def test_aion180_is_the_sole_active_authorization() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(payload)
    validate_no_go(ROOT)

    active = [record for record in payload["records"] if record["authorization_active"] is True]
    assert len(active) == 1
    record = active[0]
    assert record["authorization_transaction_id"] == SHADOW_ACTIVATION_AUTHORIZATION_ID
    assert record["approval_record_id"] == SHADOW_ACTIVATION_AUTHORIZATION_ID
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False
    assert payload["active_self_improvement_implementation_authorization_count"] == 1
    assert (
        payload["active_self_improvement_implementation_authorization"]
        == SHADOW_ACTIVATION_AUTHORIZATION_ID
    )
    assert payload["active_implementation_task"] == "AION-181"
    assert payload["formal_closeout_task"] == "AION-182"

    shadow = [
        record
        for record in payload["records"]
        if record["authorization_transaction_id"] == SHADOW_AUTHORIZATION_ID
    ][0]
    assert shadow["authorization_active"] is False
    assert shadow["authorization_consumed"] is True
    assert shadow["authorization_expired"] is True
    assert shadow["authorization_reusable"] is False

    for key in SHADOW_ACTIVATION_APPROVED_FLAGS:
        assert record[key] is True
    for key in SHADOW_ACTIVATION_PROHIBITED_FLAGS:
        assert record[key] is False


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("implementation_task", "AION-180", "activation implementation task"),
        ("authorization_scope", "runtime-activation", "activation scope"),
        ("candidate_id", "wrong-candidate", "activation candidate"),
        ("shadow_activation_enabled", True, "shadow_activation_enabled"),
        ("shadow_mode_runtime_enabled", True, "shadow_mode_runtime_enabled"),
        ("network_calls_enabled", True, "network_calls_enabled"),
        ("source_mutation_enabled", True, "source_mutation_enabled"),
        ("git_commit_creation_enabled", True, "git_commit_creation_enabled"),
        ("real_pull_request_creation_enabled", True, "real_pull_request_creation_enabled"),
        ("approval_creation_enabled", True, "approval_creation_enabled"),
        ("automatic_merge_enabled", True, "automatic_merge_enabled"),
        ("active_retrieval_promotion_enabled", True, "active_retrieval_promotion_enabled"),
        ("production_canary_enabled", True, "production_canary_enabled"),
        ("production_deployment_enabled", True, "production_deployment_enabled"),
        ("model_weight_training_enabled", True, "model_weight_training_enabled"),
    ],
)
def test_aion180_validator_rejects_no_go_mutations(field: str, value: object, message: str) -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"][-1][field] = value
    with pytest.raises(GovernanceValidationError, match=message):
        validate_authorization_ledger(payload)


def test_aion180_validator_rejects_duplicate_active_authorization() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"].append(deepcopy(payload["records"][-1]))
    with pytest.raises(GovernanceValidationError, match="record count"):
        validate_authorization_ledger(payload)


def test_aion180_validator_rejects_partial_and_extra_permission_sets() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"][-1][SHADOW_ACTIVATION_APPROVED_FLAGS[0]] = False
    with pytest.raises(GovernanceValidationError, match=SHADOW_ACTIVATION_APPROVED_FLAGS[0]):
        validate_authorization_ledger(payload)

    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"][-1]["unlisted_runtime_capability_approved"] = True
    with pytest.raises(GovernanceValidationError, match="extra approved capability"):
        validate_authorization_ledger(payload)


def test_aion180_validator_rejects_aion177_reactivation_and_soe_approval_use() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"][6]["authorization_active"] = True
    with pytest.raises(GovernanceValidationError, match="AION-180 implementation authorization"):
        validate_authorization_ledger(payload)

    payload = _json("docs/self-improvement/authorization-ledger.json")
    payload["records"][-1]["approval_record_id"] = "AION-SOE-001"
    with pytest.raises(GovernanceValidationError, match="activation approval id"):
        validate_authorization_ledger(payload)


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
