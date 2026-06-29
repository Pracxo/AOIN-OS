"""Deterministic synthetic connector dry-run simulator."""

from __future__ import annotations

from typing import Any, Protocol
from uuid import uuid4

from aion_brain.connector_simulator.hash import stable_hash
from aion_brain.connector_simulator.redaction import (
    redact_connector_simulator_payload,
)
from aion_brain.contracts.connector_simulator import (
    ConnectorSimulationRequest,
    ConnectorSimulationResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class _ConnectorShapeValidator(Protocol):
    def validate(self, connector_key: str, shape: dict[str, Any]) -> list[dict[str, Any]]:
        """Return synthetic connector shape findings."""
        ...


class ConnectorDryRunSimulator:
    """Create deterministic local-only connector simulation results."""

    def __init__(
        self,
        *,
        request_validator: _ConnectorShapeValidator,
        response_validator: _ConnectorShapeValidator,
        audit_service: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._request_validator = request_validator
        self._response_validator = response_validator
        self._audit_service = audit_service
        self._settings = settings
        self._telemetry_service = telemetry_service

    def simulate(self, request: ConnectorSimulationRequest) -> ConnectorSimulationResult:
        """Return one synthetic dry-run result without making external calls."""

        result_id = f"connector-simulation-{uuid4().hex}"
        request_findings = self._request_validator.validate(
            request.connector_key, request.request_shape
        )
        response_findings = self._response_validator.validate(
            request.connector_key, request.expected_response_shape
        )
        findings = [*request_findings, *response_findings]
        blocking_findings = [
            item for item in findings if item.get("finding_type") != "untrusted_ingress"
        ]
        blockers = [
            {
                "blocker_key": "connector_runtime_disabled",
                "status": "active",
                "bypassable": False,
            },
            {
                "blocker_key": "external_calls_disabled",
                "status": "active",
                "bypassable": False,
            },
        ]
        if blocking_findings:
            blockers.append(
                {
                    "blocker_key": "unsafe_synthetic_shape",
                    "status": "active",
                    "bypassable": False,
                }
            )
        redacted_request = redact_connector_simulator_payload(request.request_shape)
        synthetic_response = {
            "connector_key": request.connector_key,
            "simulation_type": "dry_run",
            "synthetic": True,
            "trusted": False,
            "external_calls_made": False,
            "request_fields": sorted(redacted_request.keys()),
            "response_fields": sorted(request.expected_response_shape.keys()),
            "finding_count": len(findings),
        }
        result = ConnectorSimulationResult(
            connector_simulation_result_id=result_id,
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            status="blocked" if blocking_findings else ("warning" if findings else "passed"),
            simulation_type="dry_run",
            synthetic=True,
            trusted=False,
            external_calls_made=False,
            credentials_used=False,
            tokens_used=False,
            connector_runtime_enabled=bool(
                getattr(self._settings, "connector_runtime_enabled", False)
            ),
            request_hash=stable_hash(redacted_request),
            response_hash=stable_hash(synthetic_response),
            redacted_request_shape=redacted_request,
            synthetic_response=synthetic_response,
            blockers=blockers,
            warnings=[
                {"code": "synthetic_only", "status": "open"},
                {"code": "connector_response_untrusted", "status": "open"},
            ],
            findings=findings,
            score=0.0 if blocking_findings else (0.75 if findings else 1.0),
            metadata={
                "owner_scope": request.owner_scope,
                "evidence_refs": request.evidence_refs,
                "connector_simulator_enabled": True,
                "network_call_performed": False,
                "activation_allowed": False,
            },
            created_at=utc_now(),
        )
        audit = getattr(self._audit_service, "record_simulation", None)
        if callable(audit):
            audit(result, created_by=request.created_by, owner_scope=request.owner_scope)
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_simulation_completed",
            node_type="connector_simulation",
            node_id=result.connector_simulation_result_id,
            intensity=0.85 if findings else 0.6,
            trace_id=result.trace_id,
            payload={
                "status": result.status,
                "synthetic": True,
                "external_calls_made": False,
            },
        )
        return result


__all__ = ["ConnectorDryRunSimulator"]
