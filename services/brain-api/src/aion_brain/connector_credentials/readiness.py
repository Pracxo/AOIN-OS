"""Connector credential readiness gate."""

from __future__ import annotations

from uuid import uuid4

from aion_brain.connector_credentials.architecture import ConnectorCredentialArchitectureService
from aion_brain.connector_credentials.authorization import ConnectorCredentialAuthorizationService
from aion_brain.connector_credentials.denials import ConnectorCredentialDenialService
from aion_brain.contracts.connector_credentials import (
    ConnectorCredentialReadinessRequest,
    ConnectorCredentialReadinessResult,
    utc_now,
)
from aion_brain.dialogue._shared import emit_telemetry


class ConnectorCredentialReadinessService:
    """Evaluate credential readiness without storing or reading material."""

    def __init__(
        self,
        *,
        architecture_service: ConnectorCredentialArchitectureService,
        authorization_service: ConnectorCredentialAuthorizationService,
        denial_service: ConnectorCredentialDenialService,
        audit_service: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._architecture_service = architecture_service
        self._authorization_service = authorization_service
        self._denial_service = denial_service
        self._audit_service = audit_service
        self._settings = settings
        self._telemetry_service = telemetry_service

    def evaluate(
        self,
        request: ConnectorCredentialReadinessRequest,
    ) -> ConnectorCredentialReadinessResult:
        """Return readiness evidence with credential and token paths denied."""

        readiness_enabled = bool(
            getattr(self._settings, "connector_credentials_readiness_enabled", True)
        )
        requested_actions = request.requested_scopes or [
            "connector_credentials.readiness.preview"
        ]
        blockers = _credential_blockers()
        warnings = [{"code": "connector_credential_readiness_is_not_storage", "status": "open"}]
        denied = [
            action
            for action in requested_actions
            if self._denial_service.denial_for(action) is not None
        ]
        unknown = [
            action
            for action in requested_actions
            if self._authorization_service.find(role="operator", action_key=action) is None
            and self._denial_service.denial_for(action) is None
        ]
        if denied:
            blockers.append({"blocker_key": "explicit_credential_denial_rule", "items": denied})
        if unknown:
            blockers.append({"blocker_key": "unknown_credential_action", "items": unknown})
        if not readiness_enabled:
            blockers.append({"blocker_key": "connector_credential_readiness_disabled"})

        boundary = self._architecture_service.boundary()
        result = ConnectorCredentialReadinessResult(
            connector_credential_readiness_id=f"connector-credential-readiness-{uuid4().hex}",
            trace_id=request.trace_id,
            connector_key=request.connector_key,
            status="blocked",
            credential_ready=False,
            credential_storage_allowed=False,
            token_storage_allowed=False,
            credential_access_allowed=False,
            token_access_allowed=False,
            secret_material_present=False,
            external_identity_runtime_allowed=False,
            rotation_required=True,
            revocation_required=True,
            audit_required=True,
            provenance_required=True,
            blockers=blockers,
            warnings=warnings,
            recommendations=[
                "keep_credential_store_absent_until_production_auth_exists",
                "require_rotation_revocation_audit_and_provenance_before_storage",
            ],
            metadata={
                "owner_scope": request.owner_scope,
                "requested_type": request.requested_credential_type,
                "requested_scopes": requested_actions,
                "evidence_refs": request.evidence_refs,
                "boundary_id": boundary.credential_boundary_id,
                "credential_storage_enabled": False,
                "token_storage_enabled": False,
                "secret_material_present": False,
                "external_identity_runtime_enabled": False,
                "connector_runtime_credential_access_enabled": False,
            },
            created_at=utc_now(),
        )
        record_readiness = getattr(self._audit_service, "record_readiness", None)
        if callable(record_readiness):
            record_readiness(
                readiness_id=result.connector_credential_readiness_id,
                trace_id=result.trace_id,
                actor_id=request.created_by,
                owner_scope=request.owner_scope,
                status="blocked",
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="connector_credential_readiness_checked",
            node_type="connector_credential_readiness",
            node_id=result.connector_credential_readiness_id,
            intensity=0.8,
            trace_id=result.trace_id,
            payload={"status": result.status, "credential_storage_allowed": False},
        )
        return result


def _credential_blockers() -> list[dict[str, object]]:
    return [
        {"blocker_key": "credential_store_absent", "bypassable": False},
        {"blocker_key": "token_store_absent", "bypassable": False},
        {"blocker_key": "secret_material_absent", "bypassable": False},
        {"blocker_key": "production_auth_absent", "bypassable": False},
        {"blocker_key": "external_identity_runtime_absent", "bypassable": False},
        {"blocker_key": "connector_runtime_disabled", "bypassable": False},
        {"blocker_key": "rotation_plan_required", "bypassable": False},
        {"blocker_key": "revocation_plan_required", "bypassable": False},
        {"blocker_key": "audit_provenance_required", "bypassable": False},
    ]


__all__ = ["ConnectorCredentialReadinessService"]
