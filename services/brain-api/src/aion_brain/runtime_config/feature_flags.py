"""Feature flag override service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import (
    AIONConflictException,
    AIONNotFoundException,
    AIONPolicyDeniedException,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.runtime_config import FeatureFlagOverride, FeatureFlagOverrideRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.runtime_config.profiles import _emit_runtime_config_event
from aion_brain.runtime_config.repository import RuntimeConfigRepository

_UNSAFE_FEATURE_KEYS = {
    "autonomy.full",
    "autonomy.full_control",
    "autonomy.external_tools",
    "autonomy.external_models",
    "model_gateway.external",
    "mcp.external_tools",
}


class FeatureFlagOverrideService:
    """Manage local feature flag overrides."""

    def __init__(
        self,
        repository: RuntimeConfigRepository,
        policy_adapter: PolicyAdapter,
        *,
        feature_registry: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._feature_registry = feature_registry
        self._telemetry_service = telemetry_service

    def create_override(self, request: FeatureFlagOverrideRequest) -> FeatureFlagOverride:
        """Create one feature override when safe."""
        self._authorize(
            "runtime_config.feature_override.create",
            request.owner_scope,
            actor_id=request.created_by or request.actor_id,
            risk_level="medium",
            context={"feature_key": request.feature_key, "enabled": request.enabled},
        )
        if request.enabled and _unsafe_feature(request.feature_key):
            raise AIONConflictException("unsafe_feature_override_blocked")
        self._ensure_feature_known(request.feature_key, request.owner_scope)
        now = datetime.now(UTC)
        override = FeatureFlagOverride(
            feature_override_id=request.feature_override_id or f"feature-override-{uuid4().hex}",
            feature_key=request.feature_key,
            enabled=request.enabled,
            source=request.source,
            status="active",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            owner_scope=request.owner_scope,
            reason=request.reason,
            expires_at=request.expires_at,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            disabled_at=None,
        )
        saved = self._repository.save_override(override)
        self._emit("feature_flag_override_created", saved.feature_override_id, saved.owner_scope)
        return saved

    def get_override(
        self,
        feature_override_id: str,
        scope: list[str],
    ) -> FeatureFlagOverride | None:
        """Return one override."""
        self._authorize(
            "runtime_config.feature_override.read",
            scope,
            resource_id=feature_override_id,
        )
        return self._repository.get_override(feature_override_id)

    def list_overrides(
        self,
        feature_key: str | None = None,
        status: str | None = None,
    ) -> list[FeatureFlagOverride]:
        """List feature overrides."""
        self._authorize(
            "runtime_config.feature_override.read",
            ["workspace:main"],
            context={"feature_key": feature_key, "status": status},
        )
        return self._repository.list_overrides(feature_key=feature_key, status=status)

    def disable_override(
        self,
        feature_override_id: str,
        actor_id: str | None,
        reason: str,
    ) -> FeatureFlagOverride:
        """Disable one feature override."""
        self._authorize(
            "runtime_config.feature_override.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_id=feature_override_id,
            risk_level="medium",
            context={"reason": reason},
        )
        existing = self._repository.get_override(feature_override_id)
        if existing is None:
            raise AIONNotFoundException("feature_override_not_found")
        saved = self._repository.save_override(
            existing.model_copy(
                update={
                    "status": cast(Any, "disabled"),
                    "disabled_at": datetime.now(UTC),
                    "metadata": {**existing.metadata, "disable_reason": reason},
                }
            )
        )
        self._emit("feature_flag_override_disabled", saved.feature_override_id, saved.owner_scope)
        return saved

    def expire_old(
        self,
        now: datetime | None = None,
        limit: int = 100,
    ) -> list[FeatureFlagOverride]:
        """Expire old active overrides."""
        cutoff = now or datetime.now(UTC)
        expired: list[FeatureFlagOverride] = []
        for override in self._repository.list_overrides(status="active"):
            if len(expired) >= limit:
                break
            expires_at = _aware_datetime(override.expires_at)
            if expires_at is not None and expires_at <= cutoff:
                saved = self._repository.save_override(
                    override.model_copy(
                        update={
                            "status": cast(Any, "expired"),
                            "disabled_at": cutoff,
                        }
                    )
                )
                expired.append(saved)
                self._emit(
                    "feature_flag_override_expired",
                    saved.feature_override_id,
                    saved.owner_scope,
                )
        return expired

    def effective_flags(
        self,
        scope: list[str],
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, bool]:
        """Return effective default feature flags plus active overrides."""
        self._authorize(
            "runtime_config.feature_override.read",
            scope,
            actor_id=actor_id,
            context={"workspace_id": workspace_id},
        )
        flags = self._default_flags(scope)
        for override in reversed(self._repository.list_overrides(status="active")):
            expires_at = _aware_datetime(override.expires_at)
            if expires_at is not None and expires_at <= datetime.now(UTC):
                continue
            if override.actor_id not in {None, actor_id}:
                continue
            if override.workspace_id not in {None, workspace_id}:
                continue
            flags[override.feature_key] = override.enabled
        return flags

    def _default_flags(self, scope: list[str]) -> dict[str, bool]:
        list_features = getattr(self._feature_registry, "list_features", None)
        if callable(list_features):
            try:
                features = list_features(scope)
                return {
                    str(feature.feature_key): bool(feature.default_enabled) for feature in features
                }
            except Exception:
                pass
        return {}

    def _ensure_feature_known(self, feature_key: str, scope: list[str]) -> None:
        list_features = getattr(self._feature_registry, "list_features", None)
        if not callable(list_features):
            return
        try:
            known = {str(feature.feature_key) for feature in list_features(scope)}
        except Exception:
            return
        if known and feature_key not in known:
            raise AIONNotFoundException("feature_not_found")

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
                resource_type="feature_flag_override",
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

    def _emit(self, event_type: str, node_id: str, scope: list[str]) -> None:
        _emit_runtime_config_event(
            self._telemetry_service,
            event_type=event_type,
            node_type="feature_flag",
            node_id=node_id,
            scope=scope,
            intensity=0.6,
        )


def _unsafe_feature(feature_key: str) -> bool:
    return feature_key in _UNSAFE_FEATURE_KEYS or feature_key.startswith("autonomy.full")


def _aware_datetime(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=UTC)
