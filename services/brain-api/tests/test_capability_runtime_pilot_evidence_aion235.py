from __future__ import annotations

from capability_runtime_test_support import load_runtime


def test_controlled_local_pilot_evidence_matches_required_counters() -> None:
    runtime = load_runtime()
    evidence = runtime.run_controlled_local_pilot()
    expected = dict(evidence)
    report_fingerprint = expected.pop("report_fingerprint")
    assert report_fingerprint == runtime.capability_runtime_fingerprint(expected)
    assert evidence["pilot_id"] == "AION-235-controlled-sandboxed-capability-runtime-pilot"
    assert evidence["authorization_id"] == "AION-234-SRI-0003"
    assert evidence["capability_manifest_count"] == 8
    assert evidence["connector_manifest_count"] == 1
    assert evidence["sessions_started"] == 1
    assert evidence["sessions_closed"] == 1
    assert evidence["active_sessions_after_close"] == 0
    assert evidence["requests_processed"] == 8
    assert evidence["active_requests_after_close"] == 0
    assert evidence["operator_selections_validated"] == 8
    assert evidence["policy_bindings"] == 8
    assert evidence["risk_bindings"] == 8
    assert evidence["guardrail_bindings"] == 8
    assert evidence["approval_bundles_validated"] == 3
    assert evidence["budget_decisions_passed"] == 8
    assert evidence["kill_switch_checks"] >= 16
    assert evidence["sandbox_allow_decisions"] == 8
    assert evidence["pure_reference_capability_executions"] == 6
    assert evidence["synthetic_reference_connector_simulations"] == 2
    assert evidence["write_previews_created"] == 1
    assert evidence["execution_receipts_created"] == 8
    assert evidence["output_validations_passed"] == 8
    assert evidence["execution_provenance_records"] == 8
    assert evidence["rollback_plans_created"] == 1
    assert evidence["rollbacks_completed"] == 1
    assert evidence["exact_replays_returned"] == 1
    assert evidence["changed_replays_rejected"] == 1
    assert evidence["model_output_triggered_executions_blocked"] == 1
    assert evidence["unknown_capabilities_blocked"] == 1
    assert evidence["schema_invalid_requests_blocked"] == 1
    assert evidence["temporary_files_retained"] == 0
    assert evidence["integrity_passed"] is True
    assert evidence["redacted"] is True
    assert evidence["production_effect"] is False
    assert evidence["runtime_effect"] is False
    assert all(evidence[key] == 0 for key in runtime.PROHIBITED_EFFECT_COUNTERS)
