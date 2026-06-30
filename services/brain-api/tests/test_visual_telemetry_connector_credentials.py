from __future__ import annotations

from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType
from aion_brain.telemetry.visual import CONNECTOR_CREDENTIAL_TELEMETRY_EVENTS


def test_connector_credential_visual_telemetry_events_are_registered() -> None:
    events = set(CONNECTOR_CREDENTIAL_TELEMETRY_EVENTS)

    assert "connector_credential_boundary_read" in events
    assert "connector_credential_lifecycle_read" in events
    assert "connector_credential_readiness_checked" in events
    assert "connector_secret_redaction_previewed" in events
    assert "connector_credential_boundary_read" in VisualTelemetryEventType.__args__
    assert "connector_credential_readiness" in VisualNodeType.__args__
