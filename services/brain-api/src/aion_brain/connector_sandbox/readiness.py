"""Connector sandbox readiness gate."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.connector_sandbox.capabilities import ConnectorSandboxCapabilityRuleService
from aion_brain.connector_sandbox.denials import ConnectorSandboxDenialService
from aion_brain.connector_sandbox.isolation import ConnectorIsolationBoundaryService
from aion_brain.contracts.connector_sandbox import (
    ConnectorSandboxReadinessRequest,
    ConnectorSandboxReadinessResult,
    ConnectorSandboxReadinessStatus,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorSandboxReadinessService:
    """Evaluate connector sandbox readiness without running sandboxed code."""

    def __init__(
        self,
        *,
        boundary_service: ConnectorIsolationBoundaryService,
        capability_service: ConnectorSandboxCapabilityRuleService,
        denial_service: ConnectorSandboxDenialService,
        audit_service: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._boundary_service = boundary_service
        self._capability_service = capability_service
        self._denial_service = denial_service
        self._audit_service = audit_service
        self._settings = settings
        self._telemetry_service = telemetry_service

    def evaluate(
        self,
        request: ConnectorSandboxReadinessRequest,
    ) -> ConnectorSandboxReadinessResult:
        """Return readiness evidence with all sandbox runtime permissions denied."""

        readiness_enabled = bool(
            getattr(self._settings, "connector_sandbox_readiness_enabled", True)
        )
        requested = request.requested_capabilities or ["connector.sandbox.readiness.preview"]
        blockers = _sandbox_blockers()
        warnings = [{"code": "connector_sandbox_readiness_is_not_execution", "status": "open"}]
        denied = [
            capability
            for capability in requested
            if self._denial_service.denial_for(capability) is not None
        ]
        unknown = [
            capability
            for capability in requested
            if self._capability_service.get(capability) is None
        ]
        if denied:
            blockers.append({"blocker_key": "explicit_sandbox_denial_rule", "items": denied})
        if unknown:
            blockers.append({"blocker_key": "unknown_sandbox_capability", "items": unknown})
        if not readiness_enabled:
            blockers.append({"blocker_key": "connector_sandbox_readiness_disabled"})

        sandbox_ready = readiness_enabled and not denied and not unknown
        status: ConnectorSandboxReadinessStatus = "ready" if sandbox_ready else "blocked"
        boundary = self._boundary_service.boundary()
        result = ConnectorSandboxReadinessResult(
            connector_sandbox_readiness_id=f"connector-sandbox-readiness-{uuid4().hex}",
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            status=status,
            sandbox_ready=sandbox_ready,
            runtime_execution_allowed=False,
            filesystem_access_allowed=False,
            network_access_allowed=False,
            credential_access_allowed=False,
            token_access_allowed=False,
            process_spawn_allowed=False,
            dynamic_import_allowed=False,
            package_install_allowed=False,
            connector_activation_allowed=False,
            audit_required=True,
            provenance_required=True,
            blockers=blockers,
            warnings=warnings,
            recommendations=[
                "keep_real_sandbox_runtime_absent",
                "require_release_gate_before_sandbox_execution",
            ],
            metadata={
                "owner_scope": request.owner_scope,
                "requested_capabilities": requested,
                "declared_policy_actions": request.declared_policy_actions,
                "evidence_refs": request.evidence_refs,
                "boundary_id": boundary.sandbox_boundary_id,
                "runtime_execution_allowed": False,
                "filesystem_access_allowed": False,
                "network_access_allowed": False,
                "credential_access_allowed": False,
                "token_access_allowed": False,
                "process_spawn_allowed": False,
                "dynamic_import_allowed": False,
                "package_install_allowed": False,
                "connector_activation_allowed": False,
            },
            created_at=utc_now(),
        )
        record_readiness = getattr(self._audit_service, "record_readiness", None)
        if callable(record_readiness):
            record_readiness(
                readiness_id=result.connector_sandbox_readiness_id,
                trace_id=result.trace_id,
                actor_id=request.created_by,
                owner_scope=request.owner_scope,
                status="passed" if result.sandbox_ready else "blocked",
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_sandbox_readiness_checked",
            node_type="connector_sandbox_readiness",
            node_id=result.connector_sandbox_readiness_id,
            intensity=0.65 if result.sandbox_ready else 0.8,
            trace_id=result.trace_id,
            payload={"status": result.status, "runtime_execution_allowed": False},
        )
        return result


def _sandbox_blockers() -> list[dict[str, object]]:
    return [
        {"blocker_key": "real_sandbox_runtime_absent", "bypassable": False},
        {"blocker_key": "connector_runtime_disabled", "bypassable": False},
        {"blocker_key": "runtime_execution_disabled", "bypassable": False},
        {"blocker_key": "filesystem_access_disabled", "bypassable": False},
        {"blocker_key": "network_access_disabled", "bypassable": False},
        {"blocker_key": "credentials_tokens_disabled", "bypassable": False},
        {"blocker_key": "process_spawn_disabled", "bypassable": False},
        {"blocker_key": "dynamic_import_disabled", "bypassable": False},
        {"blocker_key": "package_install_disabled", "bypassable": False},
        {"blocker_key": "activation_disabled", "bypassable": False},
    ]


__all__ = ["ConnectorSandboxReadinessService"]
