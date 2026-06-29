from __future__ import annotations

from aion_brain.connector_simulator.findings import ConnectorSimulatorFindingService


def test_connector_simulator_findings_are_safe_summaries() -> None:
    finding = ConnectorSimulatorFindingService().create(
        "mock.local.preview",
        "external_url_detected",
        source="request_shape",
    )

    assert finding.finding_type == "external_url_detected"
    assert finding.severity == "critical"
    assert finding.metadata["source"] == "request_shape"
