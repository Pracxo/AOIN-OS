from __future__ import annotations

from aion_brain.connector_simulator.response_shapes import ConnectorResponseShapeValidator


def test_connector_response_shape_validator_marks_ingress_untrusted() -> None:
    findings = ConnectorResponseShapeValidator().validate(
        "mock.local.preview",
        {"object": "synthetic_response"},
    )

    assert findings[0]["finding_type"] == "untrusted_ingress"
    assert findings[0]["metadata"]["trusted"] is False
