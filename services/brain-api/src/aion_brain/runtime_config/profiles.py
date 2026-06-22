"""Runtime configuration profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.runtime_config import ConfigProfile, ConfigProfileCreateRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.runtime_config.repository import RuntimeConfigRepository


class ConfigProfileService:
    """Manage safe runtime configuration profiles."""

    def __init__(
        self,
        repository: RuntimeConfigRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_profile(self, request: ConfigProfileCreateRequest) -> ConfigProfile:
        """Create one safe metadata profile without mutating process env."""
        self._authorize(
            "runtime_config.profile.create",
            request.owner_scope,
            actor_id=request.created_by,
            risk_level="medium",
            context={"name": request.name, "activate": request.activate},
        )
        now = datetime.now(UTC)
        profile = ConfigProfile(
            config_profile_id=request.config_profile_id or f"config-profile-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active" if request.activate else "disabled",
            profile_type=request.profile_type,
            owner_scope=request.owner_scope,
            values=request.values,
            feature_flags=request.feature_flags,
            constraints=request.constraints,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None if request.activate else now,
        )
        saved = self._repository.save_profile(profile)
        self._emit("config_profile_created", saved.config_profile_id, saved.owner_scope, 0.5)
        if saved.status == "active":
            self._emit("config_profile_activated", saved.config_profile_id, saved.owner_scope, 0.6)
        return saved

    def get_profile(self, config_profile_id: str, scope: list[str]) -> ConfigProfile | None:
        """Return one config profile."""
        self._authorize(
            "runtime_config.profile.read",
            scope,
            resource_id=config_profile_id,
        )
        return self._repository.get_profile(config_profile_id)

    def list_profiles(
        self,
        status: str | None = None,
        profile_type: str | None = None,
    ) -> list[ConfigProfile]:
        """List config profiles."""
        self._authorize(
            "runtime_config.profile.read",
            ["workspace:main"],
            context={"status": status, "profile_type": profile_type},
        )
        return self._repository.list_profiles(status=status, profile_type=profile_type)

    def disable_profile(
        self,
        config_profile_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ConfigProfile:
        """Disable one profile."""
        return self._set_status(
            config_profile_id,
            "disabled",
            actor_id,
            reason,
            "config_profile_disabled",
        )

    def activate_profile(
        self,
        config_profile_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ConfigProfile:
        """Activate one profile for metadata use only."""
        return self._set_status(
            config_profile_id,
            "active",
            actor_id,
            reason,
            "config_profile_activated",
        )

    def _set_status(
        self,
        config_profile_id: str,
        status: str,
        actor_id: str | None,
        reason: str,
        event_type: str,
    ) -> ConfigProfile:
        self._authorize(
            "runtime_config.profile.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_id=config_profile_id,
            risk_level="medium",
            context={"reason": reason, "status": status},
        )
        existing = self._repository.get_profile(config_profile_id)
        if existing is None:
            raise AIONNotFoundException("config_profile_not_found")
        now = datetime.now(UTC)
        saved = self._repository.save_profile(
            existing.model_copy(
                update={
                    "status": cast(Any, status),
                    "updated_at": now,
                    "disabled_at": now if status == "disabled" else None,
                    "metadata": {**existing.metadata, "last_status_reason": reason},
                }
            )
        )
        self._emit(event_type, saved.config_profile_id, saved.owner_scope, 0.6)
        return saved

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="runtime_config_profile",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=scope,
                context=context or {},
            )
        )
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(self, event_type: str, node_id: str, scope: list[str], intensity: float) -> None:
        _emit_runtime_config_event(
            self._telemetry_service,
            event_type=event_type,
            node_type="config",
            node_id=node_id,
            scope=scope,
            intensity=intensity,
        )


def _emit_runtime_config_event(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    intensity: float,
    payload: dict[str, Any] | None = None,
) -> None:
    emit = getattr(telemetry_service, "emit", None)
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
                edge_to=None,
                intensity=intensity,
                payload={"owner_scope": scope, **(payload or {})},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
