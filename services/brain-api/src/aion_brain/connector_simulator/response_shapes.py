"""Synthetic connector response-shape validation."""

from __future__ import annotations

from typing import Any

from aion_brain.connector_simulator.findings import ConnectorSimulatorFindingService


class ConnectorResponseShapeValidator:
    """Validate synthetic connector response shapes without trusting them."""

    def __init__(self, finding_service: ConnectorSimulatorFindingService | None = None) -> None:
        self._finding_service = finding_service or ConnectorSimulatorFindingService()

    def validate(self, connector_key: str, shape: dict[str, Any]) -> list[dict[str, Any]]:
        """Return response-shape findings."""

        findings = self._finding_service.findings_for_payload(
            connector_key, shape, source="response_shape"
        )
        findings.append(
            self._finding_service.create(
                connector_key,
                "untrusted_ingress",
                source="response_shape",
                metadata={"trusted": False},
            )
        )
        return [finding.model_dump(mode="json") for finding in findings]


__all__ = ["ConnectorResponseShapeValidator"]
