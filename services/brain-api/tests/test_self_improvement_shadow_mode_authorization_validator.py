"""AION-177 shadow-mode authorization validator tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION_178_FEATURE_COMMIT,
    AION_178_MERGE_COMMIT,
    AION_178_MERGED_AT,
    SHADOW_ACTIVATION_AUTHORIZATION_ID,
    SHADOW_APPROVED_FLAGS,
    SHADOW_AUTHORIZATION_ID,
    SHADOW_OPERATOR_EVALUATION_DECISION,
    SHADOW_OPERATOR_EVALUATION_ID,
    SHADOW_PROHIBITED_FLAGS,
    GovernanceValidationError,
    validate_authorization_ledger,
    validate_no_go,
    validate_shadow_authorization_example,
)


def test_authorization_ledger_has_closed_shadow_mode_record() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(payload)
    validate_no_go(ROOT)

    active = [record for record in payload["records"] if record["authorization_active"] is True]
    assert active == []
    assert payload["active_self_improvement_implementation_authorization_count"] == 0
    assert payload["active_self_improvement_implementation_authorization"] == "none"
    assert payload["active_implementation_task"] == "none"
    activation_record = _record(payload["records"], SHADOW_ACTIVATION_AUTHORIZATION_ID)
    assert activation_record["authorization_active"] is False
    assert activation_record["authorization_consumed"] is True
    assert activation_record["authorization_consumed_by_task"] == "AION-181"
    assert activation_record["formal_closeout_task"] == "AION-182"
    record = _record(payload["records"], SHADOW_AUTHORIZATION_ID)
    assert record["authorization_transaction_id"] == SHADOW_AUTHORIZATION_ID
    assert record["record_kind"] == "authorization_closeout"
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-178"
    assert record["authorization_consumed_by_pr"] == 89
    assert record["authorization_consumed_by_feature_commits"] == [AION_178_FEATURE_COMMIT]
    assert record["authorization_consumed_by_merge_commit"] == AION_178_MERGE_COMMIT
    assert record["authorization_consumed_at"] == AION_178_MERGED_AT
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False
    assert record["closeout_evaluation_id"] == SHADOW_OPERATOR_EVALUATION_ID
    assert record["shadow_operator_evaluation_decision"] == SHADOW_OPERATOR_EVALUATION_DECISION
    assert record["new_implementation_authorization_created"] is False
    assert record["runtime_activation_created"] is False
    for key in SHADOW_APPROVED_FLAGS:
        assert record[key] is True
    for key in SHADOW_PROHIBITED_FLAGS:
        assert record[key] is False


def test_shadow_authorization_example_matches_validator_contract() -> None:
    payload = _json("examples/self-improvement/shadow-mode-authorization.json")
    validate_shadow_authorization_example(payload)


def test_shadow_validator_rejects_runtime_enablement() -> None:
    payload = _json("docs/self-improvement/authorization-ledger.json")
    _record(payload["records"], SHADOW_AUTHORIZATION_ID)["shadow_mode_runtime_enabled"] = True
    with pytest.raises(GovernanceValidationError, match="shadow_mode_runtime_enabled"):
        validate_authorization_ledger(payload)


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload


def _record(records: list[dict[str, Any]], authorization_id: str) -> dict[str, Any]:
    matches = [
        record
        for record in records
        if record["authorization_transaction_id"] == authorization_id
    ]
    assert len(matches) == 1
    return matches[0]
