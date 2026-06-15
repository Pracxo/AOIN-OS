"""Delegation grant service."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.autonomy.modes import risk_allows
from aion_brain.autonomy.repository import AutonomyRepository
from aion_brain.contracts.autonomy import (
    AutonomyLifecycleEvent,
    DelegationGrant,
    DelegationGrantRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter


class DelegationService:
    """Manage bounded autonomy delegation grants."""

    def __init__(
        self,
        repository: AutonomyRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_grant(self, request: DelegationGrantRequest) -> DelegationGrant:
        """Create one delegation grant."""
        self._authorize(
            "autonomy.delegation.create",
            request.actor_id,
            request.workspace_id,
            request.owner_scope,
            {"mode": request.mode, "reason": request.reason},
        )
        grant = DelegationGrant(
            delegation_id=request.delegation_id or f"delegation-{uuid4().hex}",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            delegated_by=request.delegated_by,
            delegated_to=request.delegated_to,
            owner_scope=request.owner_scope,
            mode=request.mode,
            max_risk_level=request.max_risk_level,
            allowed_action_types=request.allowed_action_types,
            resource_types=request.resource_types,
            constraints=request.constraints,
            status="active",
            reason=request.reason,
            created_at=datetime.now(UTC),
            expires_at=request.expires_at,
            revoked_at=None,
        )
        saved = self._repository.save_delegation(grant)
        self._record_event("delegation_created", saved)
        return saved

    def get_grant(self, delegation_id: str, scope: list[str]) -> DelegationGrant | None:
        """Return one visible grant."""
        self._authorize("autonomy.delegation.read", None, None, scope, {}, risk_level="low")
        grant = self._repository.get_delegation(delegation_id)
        if grant is None or not _scope_matches(grant.owner_scope, scope):
            return None
        return grant

    def list_grants(
        self,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> list[DelegationGrant]:
        """List delegation grants."""
        self._authorize(
            "autonomy.delegation.read",
            actor_id,
            workspace_id,
            ["workspace:main"],
            {"status": status},
            risk_level="low",
        )
        return self._repository.list_delegations(
            actor_id=actor_id,
            workspace_id=workspace_id,
            status=status,
        )

    def revoke_grant(
        self,
        delegation_id: str,
        actor_id: str | None,
        reason: str,
    ) -> DelegationGrant:
        """Revoke one grant."""
        grant = self._repository.get_delegation(delegation_id)
        if grant is None:
            raise ValueError("delegation_not_found")
        self._authorize(
            "autonomy.delegation.revoke",
            actor_id,
            grant.workspace_id,
            grant.owner_scope,
            {"reason": reason, "delegated_by": grant.delegated_by},
        )
        saved = self._repository.save_delegation(
            grant.model_copy(
                update={"status": "revoked", "reason": reason, "revoked_at": datetime.now(UTC)}
            )
        )
        self._record_event("delegation_revoked", saved)
        return saved

    def find_active_grant(
        self,
        actor_id: str | None,
        workspace_id: str | None,
        action_type: str,
        resource_type: str,
        risk_level: str,
        scope: list[str],
    ) -> DelegationGrant | None:
        """Return the first active grant covering an action."""
        now = datetime.now(UTC)
        grants = self._repository.list_delegations(
            actor_id=actor_id,
            workspace_id=workspace_id,
            status="active",
        )
        for grant in grants:
            if grant.expires_at is not None and _aware(grant.expires_at) <= now:
                continue
            if not _scope_matches(grant.owner_scope, scope):
                continue
            if grant.allowed_action_types and action_type not in grant.allowed_action_types:
                continue
            if grant.resource_types and resource_type not in grant.resource_types:
                continue
            if not risk_allows(risk_level, grant.max_risk_level):
                continue
            return grant
        return None

    def _authorize(
        self,
        action_type: str,
        actor_id: str | None,
        workspace_id: str | None,
        scope: list[str],
        context: dict[str, object],
        *,
        risk_level: str = "medium",
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=workspace_id,
                action_type=action_type,
                resource_type="delegation",
                resource_id=None,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[],
                security_scope=scope or ["workspace:main"],
                context=context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _record_event(self, event_type: str, grant: DelegationGrant) -> None:
        event = AutonomyLifecycleEvent(
            autonomy_event_id=f"autonomy-event-{uuid4().hex}",
            delegation_id=grant.delegation_id,
            event_type=event_type,  # type: ignore[arg-type]
            actor_id=grant.actor_id,
            workspace_id=grant.workspace_id,
            payload={"mode": grant.mode, "status": grant.status},
            created_at=datetime.now(UTC),
        )
        self._repository.save_lifecycle_event(event)
        _emit(
            self._telemetry_service,
            event_type,
            "delegation",
            grant.delegation_id,
            0.7,
            event.payload,
        )


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(set(scope)))


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, object],
) -> None:
    if telemetry_service is None:
        return
    event = VisualTelemetryEvent(
        telemetry_id=f"telemetry-{node_id}-{event_type}",
        trace_id=node_id,
        event_type=event_type,  # type: ignore[arg-type]
        node_type=node_type,  # type: ignore[arg-type]
        node_id=node_id,
        edge_from=None,
        edge_to=node_id,
        intensity=intensity,
        payload=payload,
        created_at=datetime.now(UTC),
    )
    try:
        emit = getattr(telemetry_service, "emit", None)
        if callable(emit):
            emit(event)
            return
        save = getattr(telemetry_service, "save_visual_telemetry", None)
        if callable(save):
            save(event.trace_id, [event])
    except Exception:
        return
