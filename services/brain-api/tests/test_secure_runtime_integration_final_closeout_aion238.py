from __future__ import annotations

import json
from pathlib import Path

from secure_runtime_integration_final_evaluation_test_support import (
    evaluation_module,
)

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_aion238_report_closes_sri_program_and_authorization():
    module = evaluation_module()
    report = load_json(
        "examples/secure-runtime-integration/"
        "secure-runtime-integration-final-evaluation-report.json"
    )
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    auth = load_json("docs/secure-runtime-integration/authorization-ledger.json")

    module.validate_report(report)
    assert report["decision"] == module.PASS_DECISION
    assert report["scenario_count"] == 28
    assert set(report["scenario_results"].values()) == {"pass"}
    assert all(report["hard_gate_results"].values())

    assert program["program_state"] == "secure_runtime_integration_program_complete"
    assert program["secure_runtime_integration_program_complete"] is True
    assert program["secure_runtime_integration_final_evaluation_id"] == "AION-SRIPE-004"
    assert program["secure_runtime_integration_final_evaluation_decision"] == (
        module.PASS_DECISION
    )
    assert program["final_completed_task"] == "AION-238"
    assert program["active_sri_implementation_authorization_count"] == 0
    assert program["active_sri_implementation_authorization"] is None
    assert program["active_sri_implementation_task"] is None
    assert program["formal_closeout_task"] is None
    assert program["next_sri_implementation_task"] is None

    assert auth["authorization_transaction_id"] == "AION-236-SRI-0004"
    assert auth["authorization_active"] is False
    assert auth["authorization_consumed"] is True
    assert auth["authorization_consumed_by_task"] == "AION-237"
    assert auth["authorization_consumed_by_prs"] == [156]
    assert auth["authorization_consumed_by_feature_commits"] == [
        "df1f89e1708638e32aef0532fb37ed150b85b600"
    ]
    assert auth["authorization_consumed_by_merge_commits"] == [
        "55f2721bb036886a693a36d870d49f49f7ecc6d1"
    ]
    assert auth["authorization_expired"] is True
    assert auth["authorization_reusable"] is False
    assert auth["authorization_closed_by_task"] == "AION-238"
    assert auth["final_sri_evaluation_id"] == "AION-SRIPE-004"
    assert auth["final_sri_evaluation_decision"] == module.PASS_DECISION
    assert auth["active_authorizations"] == []
    assert not any(item["authorization_active"] for item in auth["records"])


def test_aion237_delivery_is_reconciled_to_merged_pr_156():
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    record = program["aion_237_record"]

    assert record["ci_result"] == "pass"
    assert record["pull_requests"] == [156]
    assert record["feature_commits"] == [
        "df1f89e1708638e32aef0532fb37ed150b85b600"
    ]
    assert record["merge_commits"] == [
        "55f2721bb036886a693a36d870d49f49f7ecc6d1"
    ]
    assert record["completion_timestamp"] == "2026-08-01T11:32:50Z"
    assert record["authorization_state"] == "consumed_by_AION-237_closed_by_AION-238"
    assert record["final_evaluation_id"] == "AION-SRIPE-004"


def test_v02_release_qualification_successor_authorization_is_exact_and_disabled():
    module = evaluation_module()
    program = load_json("docs/v02-release-qualification/program-ledger.json")
    auth = load_json("docs/v02-release-qualification/authorization-ledger.json")

    assert program["program_id"] == "AION-V02-RELEASE-QUALIFICATION-001"
    assert program["program_state"] == (
        "v02_release_qualification_program_authorized_not_implemented"
    )
    assert program["parent_evaluation_id"] == "AION-SRIPE-004"
    assert program["parent_evaluation_decision"] == module.PASS_DECISION
    assert program["active_v02_release_qualification_authorization_count"] == 1
    assert program["active_v02_release_qualification_authorization"] == (
        "AION-238-V02RQ-0001"
    )
    assert program["active_v02_release_qualification_task"] == "AION-239"
    assert program["formal_closeout_task"] == "AION-240"
    assert program["final_planned_task"] == "AION-244"

    assert auth["authorization_transaction_id"] == "AION-238-V02RQ-0001"
    assert auth["approval_record_id"] == "AION-238-V02RQ-0001"
    assert auth["implementation_task"] == "AION-239"
    assert auth["formal_closeout_task"] == "AION-240"
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False
    assert auth["active_authorizations"] == [
        {
            "authorization_transaction_id": "AION-238-V02RQ-0001",
            "implementation_task": "AION-239",
            "formal_closeout_task": "AION-240",
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
            "authorization_reusable": False,
        }
    ]
    assert all(auth["approved_capabilities"].values())
    assert not any(auth["prohibited_capabilities"].values())

    for key in auth["zero_resource_limit_keys"]:
        assert auth["resource_limits"][key] == 0
    for path in auth["future_source_scope"]:
        assert not (REPO_ROOT / path).exists()
    assert not (REPO_ROOT / "scripts/v02-release-qualification-local-run.py").exists()


def test_release_state_remains_false_and_fail_does_not_authorize_successor():
    module = evaluation_module()
    sri_program = load_json("docs/secure-runtime-integration/program-ledger.json")
    v02_program = load_json("docs/v02-release-qualification/program-ledger.json")
    v02_auth = load_json("docs/v02-release-qualification/authorization-ledger.json")

    assert sri_program["v02_release_ready"] is False
    assert sri_program["v02_tag_created"] is False
    assert sri_program["v02_release_created"] is False
    assert v02_program["v02_release_ready"] is False
    assert v02_program["v02_tag_created"] is False
    assert v02_program["v02_release_created"] is False
    assert v02_auth["parent_evaluation_decision"] == module.PASS_DECISION
    assert module.FAIL_DECISION not in json.dumps((v02_program, v02_auth), sort_keys=True)
