from __future__ import annotations

from knowledge_claim_graph_evaluation_test_helpers import evaluation_report


def test_claim_graph_evaluation_runtime_state_has_no_side_effects():
    report = evaluation_report()
    for key, value in report["runtime_state"].items():
        assert value is False, key
    security = report["security_state"]
    assert security["synthetic_evidence_only"] is True
    assert security["redacted"] is True
    assert security["source_body_present"] is False
    assert security["source_preview_present"] is False
    assert security["raw_url_present"] is False
    assert security["credential_present"] is False
    assert security["token_present"] is False
    assert security["authorization_header_present"] is False
