from __future__ import annotations

from tests.secure_runtime_test_support import pilot_evidence_payload


def test_pilot_evidence_counts_and_zero_effects_are_exact() -> None:
    evidence = pilot_evidence_payload()

    assert evidence["pilot_id"] == "AION-231-controlled-local-operator-runtime-pilot"
    assert evidence["identity_assertions_verified"] == 1
    assert evidence["replay_claims_created"] == 1
    assert evidence["exact_replays_rejected"] == 1
    assert evidence["sessions_started"] == 1
    assert evidence["sessions_closed"] == 1
    assert evidence["temporary_files_retained"] == 0
    for key in (
        "actual_capability_executions",
        "network_calls",
        "model_provider_calls",
        "connector_calls",
        "tool_executions",
        "credentials_persisted",
        "tokens_persisted",
        "production_writes",
        "glm_live_executions",
        "source_mutations",
        "git_operations",
    ):
        assert evidence[key] == 0
