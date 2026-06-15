"""Connector registry service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.connectors.repository import ConnectorRepository
from aion_brain.contracts.connectors import ConnectorCreateRequest, ConnectorDefinition
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.sandbox import SandboxValidationCheck, SandboxValidationResult
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.secrets.service import SecretRefService


class ConnectorService:
    """Manage connector definitions as metadata only."""

    def __init__(
        self,
        *,
        repository: ConnectorRepository,
        policy_adapter: PolicyAdapter,
        secret_ref_service: SecretRefService,
        telemetry_service: object | None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._secret_ref_service = secret_ref_service
        self._telemetry_service = telemetry_service

    def create_connector(self, request: ConnectorCreateRequest) -> ConnectorDefinition:
        """Create a metadata-only connector definition."""
        self._authorize(
            "connector.create",
            request.connector_id,
            "medium",
            request.owner_scope,
            actor_id=request.created_by,
            approval_present=True,
        )
        if request.auth_secret_ref_id is not None:
            secret = self._secret_ref_service.get_secret_ref(
                request.auth_secret_ref_id,
                request.owner_scope,
            )
            if secret is None:
                raise ValueError("auth_secret_ref_not_found")
        now = datetime.now(UTC)
        connector = ConnectorDefinition(
            connector_id=request.connector_id or f"connector-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active",
            connector_type=request.connector_type,
            owner_scope=request.owner_scope,
            base_endpoint_ref=request.base_endpoint_ref,
            auth_secret_ref_id=request.auth_secret_ref_id,
            allowed_actions=request.allowed_actions,
            allowed_scopes=request.allowed_scopes,
            risk_level=request.risk_level,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None,
        )
        saved = self._repository.save(connector)
        self._emit("connector_created", "connector", saved.connector_id, 0.5, {})
        return saved

    def get_connector(self, connector_id: str, scope: list[str]) -> ConnectorDefinition | None:
        """Return one connector definition without making external calls."""
        self._authorize("connector.read", connector_id, "low", scope)
        connector = self._repository.get(connector_id)
        if connector is None or not _scope_matches(connector.owner_scope, scope):
            return None
        return connector

    def list_connectors(
        self,
        scope: list[str],
        status: str | None = None,
        connector_type: str | None = None,
    ) -> list[ConnectorDefinition]:
        """List connector definitions."""
        self._authorize("connector.read", None, "low", scope)
        return [
            connector
            for connector in self._repository.list(status=status, connector_type=connector_type)
            if _scope_matches(connector.owner_scope, scope)
        ]

    def disable_connector(
        self,
        connector_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ConnectorDefinition:
        """Disable a connector definition."""
        connector = self._repository.get(connector_id)
        if connector is None:
            raise ValueError("connector_not_found")
        self._authorize(
            "connector.disable",
            connector_id,
            "medium",
            connector.owner_scope,
            actor_id=actor_id,
            approval_present=True,
        )
        now = datetime.now(UTC)
        saved = self._repository.save(
            connector.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": now,
                    "updated_at": now,
                    "metadata": {**connector.metadata, "disabled_reason": reason},
                }
            )
        )
        self._emit("connector_disabled", "connector", saved.connector_id, 0.7, {})
        return saved

    def validate_connector(
        self,
        connector_id: str,
        scope: list[str],
    ) -> SandboxValidationResult:
        """Validate connector metadata without opening a network connection."""
        self._authorize("connector.validate", connector_id, "low", scope)
        connector = self.get_connector(connector_id, scope)
        if connector is None:
            raise ValueError("connector_not_found")
        checks = [
            _check(
                "connector_status_active",
                connector.status == "active",
                "connector is active",
                "connector is not active",
                "medium",
            ),
            _check(
                "connector_metadata_only",
                connector.connector_type.endswith("_placeholder"),
                "connector is metadata-only placeholder",
                "connector type attempts live integration",
                "critical",
            ),
            _check(
                "connector_no_network_call",
                True,
                "validation performed no network call",
                "network call attempted",
                "critical",
            ),
        ]
        if connector.auth_secret_ref_id is not None:
            checks.append(
                _check(
                    "auth_secret_ref_exists",
                    self._secret_ref_service.get_secret_ref(
                        connector.auth_secret_ref_id,
                        connector.owner_scope,
                    )
                    is not None,
                    "auth secret ref exists",
                    "auth secret ref not found",
                    "high",
                )
            )
        failed = [check for check in checks if check.status == "failed"]
        failed_has_high_severity = any(
            check.severity in {"high", "critical"} for check in failed
        )
        result = SandboxValidationResult(
            validation_id=f"connector-validation-{uuid4().hex}",
            sandbox_profile_id=None,
            target_type="connector",
            target_id=connector.connector_id,
            status="failed" if failed_has_high_severity else "passed",
            score=sum(check.status == "passed" for check in checks) / len(checks),
            checks=checks,
            failures=[check.model_dump(mode="json") for check in failed],
            warnings=[],
            metadata={"connector_type": connector.connector_type},
            created_at=datetime.now(UTC),
        )
        self._emit(
            "connector_validated",
            "connector",
            connector.connector_id,
            0.8 if result.status == "passed" else 1.0,
            {"status": result.status},
        )
        return result

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        approval_present: bool = False,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="connector",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[action_type],
                security_scope=scope,
                context={},
            )
        )
        if not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type=cast(Any, event_type),
                    node_type=cast(Any, node_type),
                    node_id=node_id,
                    edge_from=None,
                    edge_to=node_id,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _check(
    check_id: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    severity: str,
) -> SandboxValidationCheck:
    return SandboxValidationCheck(
        check_id=check_id,
        name=check_id.replace("_", " "),
        status="passed" if condition else "failed",
        severity=cast(Any, severity),
        message=success_message if condition else failure_message,
        details={},
    )


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(set(requested_scope)))
