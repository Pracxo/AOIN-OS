from __future__ import annotations

from aion_brain.connector_policy.traceability import ConnectorPolicyTraceabilityService


def test_connector_policy_traceability_links_policy_matrix_and_denials() -> None:
    records = ConnectorPolicyTraceabilityService().query(
        {
            "connector_key": "mock.local.preview",
            "action_key": "connector.external.call",
        },
        ["workspace:main"],
    )

    assert len(records) == 1
    assert records[0].status == "blocked"
    assert records[0].denial_refs
    assert records[0].metadata["runtime_allowed"] is False

