"""Connector policy readiness gate for dry-run simulator work."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.contracts.connector_simulator import (
    ConnectorPolicyReadinessRequest,
    ConnectorPolicyReadinessResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry

_REQUIRED_POLICY_ACTIONS = {
    "connector_simulator.simulate",
    "connector_simulator.replay",
    "connector_simulator.policy_readiness",
}


class ConnectorPolicyReadinessService:
    """Evaluate policy readiness without approving connector runtime."""

    def __init__(
        self,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._settings = settings
        self._telemetry_service = telemetry_service

    def check(self, request: ConnectorPolicyReadinessRequest) -> ConnectorPolicyReadinessResult:
        """Return policy readiness while keeping runtime approval blocked."""

        missing = sorted(_REQUIRED_POLICY_ACTIONS - set(request.declared_policy_actions))
        sandbox_ready = request.sandbox_required
        audit_ready = request.audit_required
        provenance_ready = request.provenance_required
        policy_ready = not missing and sandbox_ready and audit_ready and provenance_ready
        blockers = [
            {
                "blocker_key": "external_calls_disabled",
                "status": "active",
                "bypassable": False,
            },
            {
                "blocker_key": "connector_activation_disabled",
                "status": "active",
                "bypassable": False,
            },
        ]
        for action in missing:
            blockers.append(
                {
                    "blocker_key": "missing_policy_action",
                    "policy_action": action,
                    "status": "active",
                    "bypassable": False,
                }
            )
        if not sandbox_ready:
            blockers.append(
                {"blocker_key": "sandbox_required", "status": "active", "bypassable": False}
            )
        result = ConnectorPolicyReadinessResult(
            connector_policy_readiness_id=f"connector-policy-readiness-{uuid4().hex}",
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            status="passed" if policy_ready else "blocked",
            policy_ready=policy_ready,
            sandbox_ready=sandbox_ready,
            audit_ready=audit_ready,
            provenance_ready=provenance_ready,
            external_calls_allowed=False,
            credentials_allowed=False,
            activation_allowed=False,
            missing_policy_actions=missing,
            blockers=blockers,
            warnings=[{"code": "policy_readiness_is_not_runtime_approval", "status": "open"}],
            recommendations=[
                "keep_connector_runtime_disabled",
                "complete_release_gate_before_external_calls",
            ],
            metadata={
                "owner_scope": request.owner_scope,
                "declared_scopes": request.declared_scopes,
                "connector_simulator_enabled": bool(
                    getattr(self._settings, "connector_simulator_enabled", True)
                ),
                "external_calls_allowed": False,
            },
            created_at=utc_now(),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_policy_readiness_checked",
            node_type="connector_policy_readiness",
            node_id=result.connector_policy_readiness_id,
            intensity=0.75 if not policy_ready else 0.55,
            trace_id=result.trace_id,
            payload={"status": result.status, "external_calls_allowed": False},
        )
        return result


__all__ = ["ConnectorPolicyReadinessService"]
