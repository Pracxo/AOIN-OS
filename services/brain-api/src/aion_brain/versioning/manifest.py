"""Version manifest service."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import (
    AIONConflictException,
    AIONNotFoundException,
    AIONPolicyDeniedException,
)
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.versioning import ReleaseChannel, VersionManifest
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import enrich_with_internal_dev_actor
from aion_brain.versioning.features import FeatureRegistryService, default_feature_entries
from aion_brain.versioning.repository import VersioningRepository


class VersionManifestService:
    """Create and freeze version manifests."""

    def __init__(
        self,
        repository: VersioningRepository,
        feature_registry: FeatureRegistryService,
        policy_adapter: PolicyAdapter,
        *,
        contract_export_service: object | None = None,
        runtime_config_status_service: object | None = None,
        config_snapshot_service: object | None = None,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._feature_registry = feature_registry
        self._policy_adapter = policy_adapter
        self._contract_export_service = contract_export_service
        self._runtime_config_status_service = runtime_config_status_service
        self._config_snapshot_service = config_snapshot_service
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_manifest(
        self,
        version: str,
        created_by: str | None,
        owner_scope: list[str],
        *,
        app: object | None = None,
    ) -> VersionManifest:
        """Create and persist a version manifest."""
        self._authorize(
            "version.manifest.create",
            owner_scope,
            actor_id=created_by,
            risk_level="medium",
            context={"version": version},
        )
        features = self._feature_registry.list_features(owner_scope)
        if not features:
            features = default_feature_entries(owner_scope)
        feature_flags = {feature.feature_key: feature.default_enabled for feature in features}
        active_profile_name: str | None = None
        runtime_status = self._runtime_config_status(owner_scope)
        if runtime_status is not None:
            feature_flags.update(runtime_status.effective_feature_flags)
            if runtime_status.active_profile is not None:
                active_profile_name = runtime_status.active_profile.name
        config_hash = self._config_hash(owner_scope, created_by)
        contract_export = self._contract_export(app)
        contract_hash = stable_hash(contract_export)
        manifest = VersionManifest(
            version_manifest_id=f"version-manifest-{uuid4().hex}",
            version=version,
            release_channel=cast(ReleaseChannel, self._settings.aion_release_channel),
            status="active",
            api_version=self._settings.api_version,
            sdk_version=_sdk_version(),
            schema_version=version,
            contract_hash=contract_hash,
            feature_flags=feature_flags,
            adapter_matrix=adapter_matrix(self._settings),
            metadata={
                "contract_count": len(contract_export.get("contracts", {})),
                "config_hash": config_hash,
                "active_config_profile": active_profile_name,
            },
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_manifest(manifest)
        self._emit(
            "version_manifest_created",
            saved.version_manifest_id,
            owner_scope,
            {"version": saved.version},
            intensity=0.5,
        )
        return saved

    def get_manifest(self, version: str, scope: list[str]) -> VersionManifest | None:
        """Return the latest manifest for a version."""
        self._authorize("version.manifest.read", scope, resource_id=version)
        return self._repository.get_manifest(version)

    def list_manifests(
        self,
        scope: list[str],
        *,
        status: str | None = None,
    ) -> list[VersionManifest]:
        """List version manifests."""
        self._authorize("version.manifest.read", scope, context={"status": status})
        return self._repository.list_manifests(status=status)

    def freeze_manifest(
        self,
        version: str,
        actor_id: str | None,
        reason: str,
        scope: list[str],
    ) -> VersionManifest:
        """Freeze a manifest after a passed freeze gate."""
        self._authorize(
            "version.manifest.freeze",
            scope,
            actor_id=actor_id,
            resource_id=version,
            risk_level="medium",
            context={"reason": reason},
        )
        manifest = self._repository.get_manifest(version)
        if manifest is None:
            raise AIONNotFoundException("version_manifest_not_found")
        if self._repository.latest_passed_freeze_gate(version) is None:
            raise AIONConflictException("freeze_gate_pass_required")
        saved = self._repository.save_manifest(
            manifest.model_copy(
                update={
                    "status": "frozen",
                    "metadata": {**manifest.metadata, "freeze_reason": reason},
                }
            )
        )
        self._emit(
            "version_manifest_frozen",
            saved.version_manifest_id,
            scope,
            {"version": saved.version},
            intensity=0.9,
        )
        return saved

    def _contract_export(self, app: object | None) -> dict[str, Any]:
        export_contracts = getattr(self._contract_export_service, "export_contracts", None)
        if callable(export_contracts) and app is not None:
            try:
                exported = export_contracts(app)
                if hasattr(exported, "model_dump"):
                    return cast(dict[str, Any], exported.model_dump(mode="json"))
            except Exception:
                pass
        return {
            "version": self._settings.version,
            "contracts": _fallback_contract_schemas(),
        }

    def _runtime_config_status(self, scope: list[str]) -> Any | None:
        status = getattr(self._runtime_config_status_service, "status", None)
        if not callable(status):
            return None
        try:
            return status(scope)
        except Exception:
            return None

    def _config_hash(self, scope: list[str], created_by: str | None) -> str | None:
        create_snapshot = getattr(self._config_snapshot_service, "create_snapshot", None)
        if not callable(create_snapshot):
            return None
        from aion_brain.contracts.runtime_config import ConfigSnapshotRequest

        try:
            snapshot = create_snapshot(
                ConfigSnapshotRequest(
                    snapshot_type="release_candidate",
                    owner_scope=scope,
                    metadata={"source": "version_manifest"},
                    created_by=created_by,
                )
            )
        except Exception:
            return None
        config_hash = getattr(snapshot, "config_hash", None)
        return config_hash if isinstance(config_hash, str) else None

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
            resource_type="version_manifest",
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

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, Any],
        *,
        intensity: float,
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
                    node_type="version",
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=intensity,
                    payload={"owner_scope": scope, **payload},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def adapter_matrix(settings: Settings) -> dict[str, Any]:
    """Return AION's provider-neutral adapter matrix."""
    return {
        "required": {
            "postgres": True,
            "redis": True,
            "nats": True,
            "opa": True,
            "local_reasoning": True,
        },
        "optional": {
            "turbovec": False,
            "graphiti": False,
            "mcp": bool(getattr(settings, "mcp_enabled", False)),
            "temporal": False,
            "litellm": bool(getattr(settings, "model_gateway_enabled", False)),
            "minio": settings.default_object_store == "minio",
            "langfuse": settings.observability_adapter == "langfuse",
        },
        "defaults": {
            "semantic_adapter": settings.default_semantic_adapter,
            "embedding_adapter": settings.embedding_adapter,
            "object_store": settings.default_object_store,
            "observability": settings.observability_adapter,
        },
    }


def stable_hash(value: Any) -> str:
    """Return a deterministic SHA-256 hash for JSON-compatible values."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _fallback_contract_schemas() -> dict[str, Any]:
    """Return core contract schemas without making import-time kernel cycles."""
    try:
        from aion_brain.kernel.contract_export import CORE_CONTRACTS

        return {contract.__name__: contract.model_json_schema() for contract in CORE_CONTRACTS}
    except Exception:
        return {"VersionManifest": VersionManifest.model_json_schema()}


def _sdk_version() -> str:
    try:
        from importlib.metadata import version

        return version("aion-sdk-python")
    except Exception:
        return "0.1.0"
