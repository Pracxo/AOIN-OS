from __future__ import annotations

from aion_brain.connector_simulator.request_shapes import ConnectorShapeValidator


def test_connector_request_shape_validator_reports_unsafe_shape() -> None:
    findings = ConnectorShapeValidator().validate(
        "mock.local.preview",
        {"endpoint": "external"},
    )

    assert findings[0]["finding_type"] == "external_url_detected"
    assert findings[0]["connector_key"] == "mock.local.preview"
