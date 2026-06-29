"""Synthetic connector request-shape validation."""

from __future__ import annotations

from typing import Any

from aion_brain.connector_simulator.findings import ConnectorSimulatorFindingService


class ConnectorShapeValidator:
    """Validate synthetic connector request shapes without executing them."""

    def __init__(self, finding_service: ConnectorSimulatorFindingService | None = None) -> None:
        self._finding_service = finding_service or ConnectorSimulatorFindingService()

    def validate(self, connector_key: str, shape: dict[str, Any]) -> list[dict[str, Any]]:
        """Return request-shape findings."""

        return [
            finding.model_dump(mode="json")
            for finding in self._finding_service.findings_for_payload(
                connector_key, shape, source="request_shape"
            )
        ]


__all__ = ["ConnectorShapeValidator"]
