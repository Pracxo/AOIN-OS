from aion234_test_support import load_json


def test_aion234_record_remains_reconciled_after_aion235() -> None:
    program = load_json("docs/secure-runtime-integration/program-ledger.json")
    record = program["aion_234_record"]
    assert record["task_id"] == "AION-234"
    assert record["branch"] == "phase/model-gateway-evaluation-capability-runtime-authorization"
    assert record["harness_commit"] == "fde592f0991244599a7471407cefc53ea0e4603d"
    assert record["closeout_commit"] == "08ae85256bb08a7c9be9e1dc9a9de887f2ad3f2a"
    assert record["ci_fix_commit"] == "be4ce1a2e77c7dd14f4775d9d8a1d3697ff3782b"
    assert record["pull_requests"] == [153]
    assert record["merge_commits"] == ["74c6ecc93333518a353bd4c69ad8823d7a47afd8"]
    assert record["ci_result"] == "pass"
    assert record["completion_timestamp"] == "2026-07-31T19:49:32Z"
    assert record["authorization_state"] == "active_for_AION-235_formal_closeout_AION-236"
    assert program["active_sri_implementation_authorization"] == "AION-234-SRI-0003"
    assert program["active_sri_implementation_task"] == "AION-235"
    assert program["formal_closeout_task"] == "AION-236"
    assert program["sandboxed_capability_runtime_authorized"] is True
    assert program["external_connector_execution_enabled"] is False
    assert program["external_tool_execution_enabled"] is False
    assert program["production_runtime_authorized"] is False
    assert program["v02_release_ready"] is False
