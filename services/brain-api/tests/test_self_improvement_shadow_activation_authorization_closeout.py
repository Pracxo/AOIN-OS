"""AION-182 authorization-closeout ledger tests."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "scripts" / "lib"

if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from self_improvement_governance import (  # noqa: E402
    GovernanceValidationError,
    validate_authorization_ledger,
)
from self_improvement_shadow_activation_operator_evaluation import PASS_DECISION  # noqa: E402


def _ledger() -> dict:
    return json.loads((ROOT / "docs/self-improvement/authorization-ledger.json").read_text())


def _aion_180_record(ledger: dict) -> dict:
    matches = [
        record
        for record in ledger["records"]
        if record.get("authorization_transaction_id") == "AION-180-SI-0007"
    ]
    assert len(matches) == 1
    return matches[0]


def test_aion_180_authorization_is_closed_and_non_reusable() -> None:
    ledger = _ledger()
    validate_authorization_ledger(ledger)
    record = _aion_180_record(ledger)

    assert (
        ledger["current_stage"]
        == "shadow_activation_control_plane_operator_evaluation_passed_disabled"
    )
    assert ledger["active_self_improvement_implementation_authorization_count"] == 0
    assert ledger["active_self_improvement_implementation_authorization"] == "none"
    assert ledger["active_implementation_task"] == "none"
    assert ledger["new_implementation_authorization_created"] is False
    assert record["record_kind"] == "authorization_closeout"
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-181"
    assert record["authorization_consumed_by_pr"] == 92
    assert record["authorization_consumed_by_feature_commits"] == [
        "c7c7a5c83606399dff2221bd7f847ea00e177603"
    ]
    assert (
        record["authorization_consumed_by_merge_commit"]
        == "e9374853a53cd098096ed50da0fabb5874152d54"
    )
    assert record["authorization_expired"] is True
    assert record["authorization_reusable"] is False


def test_aion_sace_is_not_approval_or_new_authorization() -> None:
    ledger = _ledger()
    record = _aion_180_record(ledger)

    assert record["control_plane_operator_evaluation_id"] == "AION-SACE-001"
    assert record["control_plane_operator_evaluation_decision"] == PASS_DECISION
    assert record["control_plane_operator_evaluation_used_as_approval"] is False
    assert record["control_plane_operator_evaluation_reusable"] is False
    assert record["control_plane_operator_evaluation_created_implementation_authorization"] is False
    assert record["control_plane_operator_evaluation_created_activation_approval"] is False
    assert record["control_plane_operator_evaluation_created_actual_activation"] is False
    assert record["shadow_activation_enabled"] is False
    assert record["actual_activation_available"] is False


def test_closed_aion_180_authorization_cannot_reactivate() -> None:
    ledger = _ledger()
    mutated = copy.deepcopy(ledger)
    record = _aion_180_record(mutated)
    record["authorization_active"] = True
    mutated["active_self_improvement_implementation_authorization_count"] = 1
    mutated["active_self_improvement_implementation_authorization"] = "AION-180-SI-0007"
    mutated["active_implementation_task"] = "AION-181"

    with pytest.raises(GovernanceValidationError):
        validate_authorization_ledger(mutated)
