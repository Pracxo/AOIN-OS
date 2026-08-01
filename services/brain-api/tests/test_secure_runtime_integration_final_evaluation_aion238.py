from __future__ import annotations

from copy import deepcopy

import pytest
from secure_runtime_integration_final_evaluation_test_support import (
    assert_scenario_passes,
    evaluation_module,
    evaluation_report,
)


def test_final_evaluation_report_schema_and_exact_decision():
    module = evaluation_module()
    report = evaluation_report()

    assert report["evaluation_id"] == "AION-SRIPE-004"
    assert report["evaluation_type"] == "secure_runtime_integration_program_final_evaluation"
    assert report["program_id"] == "AION-SECURE-RUNTIME-INTEGRATION-001"
    assert report["implementation_task"] == "AION-237"
    assert report["closeout_task"] == "AION-238"
    assert report["decision"] == module.PASS_DECISION
    assert report["evaluation_passed"] is True
    assert report["synthetic"] is True
    assert report["read_only"] is True
    assert report["redacted"] is True


def test_final_evaluation_executes_exactly_28_scenarios():
    module = evaluation_module()
    report = evaluation_report()

    assert report["scenario_count"] == 28
    assert tuple(report["scenario_ids"]) == module.SCENARIO_IDS
    assert tuple(item["scenario_id"] for item in report["scenarios"]) == module.SCENARIO_IDS
    assert len(set(report["scenario_ids"])) == 28
    assert set(report["scenario_results"].values()) == {"pass"}


def test_final_evaluation_rejects_duplicate_missing_unknown_scenarios():
    module = evaluation_module()
    report = evaluation_report()

    duplicate = deepcopy(report)
    duplicate["scenarios"][1] = deepcopy(duplicate["scenarios"][0])
    duplicate["report_fingerprint"] = module.fingerprint(
        {key: value for key, value in duplicate.items() if key != "report_fingerprint"}
    )
    with pytest.raises(SystemExit):
        module.validate_report(duplicate)

    missing = deepcopy(report)
    missing["scenarios"] = missing["scenarios"][:-1]
    missing["scenario_count"] = 27
    missing["report_fingerprint"] = module.fingerprint(
        {key: value for key, value in missing.items() if key != "report_fingerprint"}
    )
    with pytest.raises(SystemExit):
        module.validate_report(missing)

    unknown = deepcopy(report)
    unknown["scenarios"][0]["scenario_id"] = "unknown_scenario"
    unknown["scenario_ids"][0] = "unknown_scenario"
    unknown["report_fingerprint"] = module.fingerprint(
        {key: value for key, value in unknown.items() if key != "report_fingerprint"}
    )
    with pytest.raises(SystemExit):
        module.validate_report(unknown)


def test_final_evaluation_rejects_pass_when_hard_gate_fails():
    module = evaluation_module()
    report = deepcopy(evaluation_report())
    report["hard_gate_results"]["pilot_fingerprint_valid"] = False
    report["hard_gates"]["pilot_fingerprint_valid"] = False
    report["report_fingerprint"] = module.fingerprint(
        {key: value for key, value in report.items() if key != "report_fingerprint"}
    )

    with pytest.raises(SystemExit):
        module.validate_report(report)


def test_delivery_reconciliation_and_pilot_fingerprint():
    report = evaluation_report()

    assert report["implementation_prs"] == [156]
    assert report["implementation_feature_commits"] == [
        "df1f89e1708638e32aef0532fb37ed150b85b600"
    ]
    assert report["implementation_merge_commits"] == [
        "55f2721bb036886a693a36d870d49f49f7ecc6d1"
    ]
    assert report["pilot_validation"]["report_fingerprint"] == (
        "e54ea6886c6d7f56c1de568983515944b1b72b3dc2d8f59b310039bb96ed5035"
    )
    assert report["pilot_validation"]["report_fingerprint_valid"] is True


def test_route_static_asset_and_security_header_scenarios_pass():
    assert_scenario_passes("exact_route_and_static_asset_manifests")
    assert_scenario_passes("security_headers_csp_and_browser_non_persistence")
    report = evaluation_report()
    integrity = report["operator_console_integrity"]
    assert integrity["routes_exact"] is True
    assert integrity["static_assets_exact"] is True
    assert integrity["security_headers_exact"] is True


def test_host_origin_nonce_session_and_parser_scenarios_pass():
    for scenario_id in (
        "host_origin_and_fetch_metadata_policy",
        "bounded_http_parser_and_protocol_smuggling",
        "mutation_nonce_lifecycle",
        "session_bootstrap_lifecycle_and_limits",
        "kill_switch_and_session_close_terminal_semantics",
        "complete_listener_session_request_nonce_and_fixture_cleanup",
    ):
        assert_scenario_passes(scenario_id)


def test_model_capability_connector_and_write_preview_scenarios_pass():
    for scenario_id in (
        "deterministic_text_model_integration",
        "deterministic_structured_model_integration",
        "model_output_non_authority_and_operator_selection",
        "reference_capability_integration",
        "synthetic_connector_read_and_write_preview",
        "policy_risk_guardrail_approval_and_budget_precedence",
        "idempotency_and_replay_controls",
        "receipt_audit_provenance_and_integrity_chains",
    ):
        assert_scenario_passes(scenario_id)


def test_cleanup_zero_effects_and_successor_readiness():
    for scenario_id in (
        "concurrency_backpressure_and_performance",
        "static_console_offline_fallback_live_activation_and_accessibility",
        "zero_external_and_production_effects",
        "secure_runtime_integration_program_lineage_and_completion_readiness",
        "v02_release_qualification_program_authorization_readiness",
    ):
        assert_scenario_passes(scenario_id)
    report = evaluation_report()
    assert report["active_listeners_after_evaluation"] == 0
    assert report["active_sessions_after_evaluation"] == 0
    assert report["active_requests_after_evaluation"] == 0
    for key in evaluation_module().ZERO_EFFECT_FIELDS:
        assert report[key] == 0
    assert report["repository_unchanged"] is True
    assert report["temporary_evaluation_data_cleaned"] is True
