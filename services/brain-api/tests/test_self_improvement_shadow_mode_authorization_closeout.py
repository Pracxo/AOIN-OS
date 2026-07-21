"""AION-179 authorization closeout tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION_178_FEATURE_COMMIT,
    AION_178_MERGE_COMMIT,
    AION_178_MERGED_AT,
    SHADOW_ACTIVATION_AUTHORIZATION_ID,
    SHADOW_AUTHORIZATION_ID,
    SHADOW_OPERATOR_EVALUATION_DECISION,
    SHADOW_OPERATOR_EVALUATION_ID,
    validate_authorization_ledger,
    validate_program_ledger,
)


def test_aion_177_shadow_authorization_is_closed_by_aion_179() -> None:
    ledger = _json("docs/self-improvement/authorization-ledger.json")
    validate_authorization_ledger(ledger)

    assert ledger["current_stage"] in {
        "shadow_activation_control_plane_implemented_disabled_pending_closeout",
        "shadow_activation_control_plane_operator_evaluation_passed_disabled",
        "shadow_activation_control_plane_operator_evaluation_failed_disabled",
    }
    if (
        ledger["current_stage"]
        == "shadow_activation_control_plane_implemented_disabled_pending_closeout"
    ):
        assert ledger["active_self_improvement_implementation_authorization_count"] == 1
        assert (
            ledger["active_self_improvement_implementation_authorization"]
            == SHADOW_ACTIVATION_AUTHORIZATION_ID
        )
        assert ledger["active_implementation_task"] == "AION-181"
    else:
        assert ledger["active_self_improvement_implementation_authorization_count"] == 0
        assert ledger["active_self_improvement_implementation_authorization"] == "none"
        assert ledger["active_implementation_task"] == "none"
    activation_record = _record(ledger["records"], SHADOW_ACTIVATION_AUTHORIZATION_ID)
    assert activation_record["shadow_activation_control_plane_implemented"] is True
    assert (
        activation_record["shadow_activation_control_plane_state"]
        == "implemented_disabled_simulation_only"
    )
    assert activation_record["shadow_activation_enabled"] is False
    assert activation_record["actual_activation_available"] is False

    record = _record(ledger["records"], SHADOW_AUTHORIZATION_ID)
    assert record["record_kind"] == "authorization_closeout"
    assert record["authorization_active"] is False
    assert record["authorization_consumed"] is True
    assert record["authorization_consumed_by_task"] == "AION-178"
    assert record["authorization_consumed_by_pr"] == 89
    assert record["authorization_consumed_by_feature_commits"] == [AION_178_FEATURE_COMMIT]
    assert record["authorization_consumed_by_merge_commit"] == AION_178_MERGE_COMMIT
    assert record["authorization_consumed_at"] == AION_178_MERGED_AT
    assert record["closeout_evaluation_id"] == SHADOW_OPERATOR_EVALUATION_ID
    assert record["shadow_operator_evaluation_decision"] == SHADOW_OPERATOR_EVALUATION_DECISION
    assert record["new_implementation_authorization_created"] is False
    assert record["runtime_activation_created"] is False


def test_program_ledger_records_aion_178_completion_and_aion_179_closeout() -> None:
    program = _json("docs/self-improvement/program-ledger.json")
    validate_program_ledger(program)

    aion178 = _task(program["records"], "AION-178")
    assert aion178["feature_commits"] == [AION_178_FEATURE_COMMIT]
    assert aion178["pull_requests"] == [89]
    assert aion178["merge_commits"] == [AION_178_MERGE_COMMIT]
    assert aion178["ci_result"] == "pass"
    assert aion178["completion_timestamp"] == AION_178_MERGED_AT

    aion179 = _task(program["records"], "AION-179")
    assert aion179["authorization_state"] == "consumed_by_AION-178_closed_by_AION-179"
    assert aion179["runtime_state"] == "shadow_mode_operator_evaluation_passed_runtime_disabled"
    assert aion179["next_task"] == "AION-180"
    assert aion179["ci_result"] == "pass"


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


def _task(records: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
    matches = [record for record in records if record["task_id"] == task_id]
    assert len(matches) == 1
    return matches[0]
