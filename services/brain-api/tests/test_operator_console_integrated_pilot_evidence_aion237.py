from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts.operator_console_integration import (
    AUTHORIZATION_TRANSACTION_ID,
    LOOPBACK_BIND_HOST,
    PROHIBITED_COUNTER_NAMES,
)
from aion_brain.operator_console_runtime.evidence import evidence_report_fingerprint

REPO_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = (
    REPO_ROOT
    / "examples/secure-runtime-integration/"
    "operator-console-integrated-local-runtime-pilot-evidence.json"
)


def test_committed_integrated_pilot_evidence_is_redacted_and_fingerprinted():
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    expected = evidence_report_fingerprint(payload)

    assert payload["report_fingerprint"] == expected
    assert payload["authorization_id"] == AUTHORIZATION_TRANSACTION_ID
    assert payload["bind_host"] == LOOPBACK_BIND_HOST
    assert payload["ephemeral_port_used"] is True
    assert payload["actual_port_retained"] is False
    assert payload["redacted"] is True
    assert payload["production_effect"] is False
    assert payload["runtime_effect"] is False


def test_committed_integrated_pilot_evidence_counters_match_acceptance():
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))

    assert payload["loopback_listeners_started"] == 1
    assert payload["loopback_listeners_closed"] == 1
    assert payload["public_listeners_started"] == 0
    assert payload["normal_sessions_started"] == 1
    assert payload["normal_sessions_closed"] == 1
    assert payload["kill_control_sessions_started"] == 1
    assert payload["kill_control_sessions_killed"] == 1
    assert payload["active_sessions_after_close"] == 0
    assert payload["active_requests_after_close"] == 0
    assert payload["bootstrap_reads"] == 2
    assert payload["model_text_simulations"] == 1
    assert payload["model_structured_simulations"] == 1
    assert payload["reference_capability_executions"] == 3
    assert payload["synthetic_connector_simulations"] == 2
    assert payload["write_previews_created"] == 1
    assert payload["writes_applied"] == 0
    assert payload["mutation_nonces_issued"] == 2
    assert payload["mutation_nonce_rotations"] == 8
    assert payload["stale_nonces_rejected"] == 1
    assert payload["origin_mismatches_rejected"] == 1
    assert payload["host_mismatches_rejected"] == 1
    assert payload["model_output_triggered_executions_blocked"] == 1
    assert payload["kill_switch_activations"] == 1
    assert payload["requests_blocked_by_kill_switch"] >= 1
    assert payload["pilot_loopback_http_requests"] <= 50
    assert payload["pilot_action_requests"] <= 16
    assert payload["listener_closed"] is True
    assert payload["temporary_files_retained"] == 0
    assert payload["all_prohibited_effect_counters_zero"] is True
    for key in PROHIBITED_COUNTER_NAMES:
        assert payload[key] == 0
        assert payload["prohibited_effect_counters"][key] == 0
