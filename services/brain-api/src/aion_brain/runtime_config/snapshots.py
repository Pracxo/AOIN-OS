"""Runtime configuration snapshot service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.runtime_config import ConfigSnapshot, ConfigSnapshotRequest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import enrich_with_internal_dev_actor
from aion_brain.runtime_config.drift import compare_config_snapshots
from aion_brain.runtime_config.hash import hash_config_snapshot
from aion_brain.runtime_config.profiles import _emit_runtime_config_event
from aion_brain.runtime_config.redaction import sanitize_config_dict
from aion_brain.runtime_config.repository import RuntimeConfigRepository


class ConfigSnapshotService:
    """Create and compare redacted runtime configuration snapshots."""

    def __init__(
        self,
        repository: RuntimeConfigRepository,
        policy_adapter: PolicyAdapter,
        *,
        feature_override_service: object | None = None,
        settings: Settings | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._feature_override_service = feature_override_service
        self._settings = settings or get_settings()
        self._telemetry_service = telemetry_service

    def create_snapshot(self, request: ConfigSnapshotRequest) -> ConfigSnapshot:
        """Capture a redacted snapshot without reading or mutating process env."""
        self._authorize(
            "runtime_config.snapshot.create",
            request.owner_scope,
            actor_id=request.created_by,
            risk_level="medium",
            context={"snapshot_type": request.snapshot_type},
        )
        settings = sanitize_config_dict(self._settings.model_dump(mode="json"))
        feature_flags = (
            self._effective_flags(request.owner_scope) if request.include_feature_flags else {}
        )
        adapter_status = self._adapter_status() if request.include_adapter_status else {}
        config_hash = hash_config_snapshot(settings, feature_flags, adapter_status)
        drift: dict[str, Any] = {}
        if request.compare_to_snapshot_id:
            previous = self._repository.get_snapshot(request.compare_to_snapshot_id)
            if previous is not None:
                drift = compare_config_snapshots(
                    _snapshot_payload(previous),
                    {
                        "settings": settings,
                        "feature_flags": feature_flags,
                        "adapter_status": adapter_status,
                    },
                )
        snapshot = ConfigSnapshot(
            config_snapshot_id=request.config_snapshot_id or f"config-snapshot-{uuid4().hex}",
            snapshot_type=request.snapshot_type,
            status="active",
            owner_scope=request.owner_scope,
            settings=settings,
            feature_flags=feature_flags,
            adapter_status=adapter_status,
            config_hash=config_hash,
            drift_from_snapshot_id=request.compare_to_snapshot_id,
            drift=drift,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_snapshot(snapshot)
        self._emit("config_snapshot_created", saved.config_snapshot_id, saved.owner_scope, 0.5)
        if drift.get("has_drift"):
            self._emit("config_drift_detected", saved.config_snapshot_id, saved.owner_scope, 0.8)
        return saved

    def get_snapshot(self, config_snapshot_id: str, scope: list[str]) -> ConfigSnapshot | None:
        """Return one snapshot."""
        self._authorize(
            "runtime_config.snapshot.read",
            scope,
            resource_id=config_snapshot_id,
        )
        return self._repository.get_snapshot(config_snapshot_id)

    def list_snapshots(
        self,
        snapshot_type: str | None = None,
        limit: int = 50,
    ) -> list[ConfigSnapshot]:
        """List snapshots."""
        self._authorize(
            "runtime_config.snapshot.read",
            ["workspace:main"],
            context={"snapshot_type": snapshot_type, "limit": limit},
        )
        return self._repository.list_snapshots(snapshot_type=snapshot_type, limit=limit)

    def compare(self, snapshot_id_a: str, snapshot_id_b: str) -> dict[str, Any]:
        """Compare two persisted snapshots."""
        self._authorize(
            "runtime_config.snapshot.read",
            ["workspace:main"],
            context={"snapshot_id_a": snapshot_id_a, "snapshot_id_b": snapshot_id_b},
        )
        first = self._repository.get_snapshot(snapshot_id_a)
        second = self._repository.get_snapshot(snapshot_id_b)
        if first is None or second is None:
            raise AIONNotFoundException("config_snapshot_not_found")
        return compare_config_snapshots(_snapshot_payload(first), _snapshot_payload(second))

    def _effective_flags(self, scope: list[str]) -> dict[str, bool]:
        effective_flags = getattr(self._feature_override_service, "effective_flags", None)
        if callable(effective_flags):
            try:
                return dict(effective_flags(scope))
            except Exception:
                return {}
        return {}

    def _adapter_status(self) -> dict[str, Any]:
        return {
            "semantic_memory_adapter": self._settings.default_semantic_adapter,
            "graph_memory_adapter": self._settings.default_graph_memory_adapter,
            "model_gateway": bool(self._settings.model_gateway_enabled),
            "mcp": bool(self._settings.mcp_enabled),
            "temporal": bool(self._settings.temporal_enabled),
            "sandbox": bool(self._settings.sandbox_control_plane_enabled),
            "backups": bool(self._settings.backups_enabled),
            "release_package": bool(self._settings.release_packaging_enabled),
            "security_baseline": bool(self._settings.security_baseline_enabled),
        }

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
        policy_request = PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=actor_id,
            workspace_id=None,
            action_type=action_type,
            resource_type="config_snapshot",
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
        policy_request = enrich_with_internal_dev_actor(
            policy_request,
            self._settings,
            scope=scope,
            permissions=[action_type],
        )
        decision = self._policy_adapter.authorize(policy_request)
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(self, event_type: str, node_id: str, scope: list[str], intensity: float) -> None:
        node_type = "config_drift" if event_type == "config_drift_detected" else "config_snapshot"
        _emit_runtime_config_event(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            scope=scope,
            intensity=intensity,
        )


def _snapshot_payload(snapshot: ConfigSnapshot) -> dict[str, Any]:
    return {
        "settings": snapshot.settings,
        "feature_flags": snapshot.feature_flags,
        "adapter_status": snapshot.adapter_status,
    }
