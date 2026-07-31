from __future__ import annotations

import json
from pathlib import Path

from aion_brain.contracts.model_gateway import model_gateway_fingerprint

ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = (
    ROOT
    / "examples/secure-runtime-integration/model-gateway-local-simulation-pilot-evidence.json"
)


def test_pilot_evidence_records_required_counts_and_zero_effects() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    fingerprint = payload["report_fingerprint"]
    assert fingerprint == model_gateway_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    assert payload["pilot_id"] == "AION-233-controlled-model-gateway-simulation-pilot"
    assert payload["provider_manifest_count"] == 1
    assert payload["model_manifest_count"] == 2
    assert payload["gateway_sessions_started"] == 1
    assert payload["gateway_sessions_closed"] == 1
    assert payload["requests_processed"] == 2
    assert payload["text_simulation_requests"] == 1
    assert payload["structured_simulation_requests"] == 1
    assert payload["exact_replays_returned"] == 1
    assert payload["changed_replays_rejected"] == 1
    assert payload["protected_material_requests_blocked"] == 1
    assert payload["smuggled_action_outputs_blocked"] >= 1
    assert payload["temporary_files_retained"] == 0
    for key in (
        "actual_model_provider_calls",
        "network_calls",
        "provider_sdk_calls",
        "provider_credentials_read",
        "authorization_headers_created",
        "live_model_sessions",
        "tool_calls",
        "function_calls",
        "connector_calls",
        "actual_tool_executions",
        "prompts_persisted",
        "model_responses_persisted",
        "hidden_reasoning_records",
        "provider_raw_payloads_retained",
        "production_memory_writes",
        "production_policy_mutations",
        "belief_creations",
        "belief_mutations",
        "deployments",
        "model_weight_changes",
    ):
        assert payload[key] == 0
