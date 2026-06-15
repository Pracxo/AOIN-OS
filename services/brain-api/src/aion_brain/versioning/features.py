"""Feature registry defaults and service."""

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException, AIONPolicyDeniedException
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.versioning import FeatureCategory, FeatureRegistryEntry
from aion_brain.policy.base import PolicyAdapter
from aion_brain.versioning.repository import VersioningRepository

DEFAULT_FEATURE_SPECS: tuple[tuple[str, str, bool, bool], ...] = (
    ("kernel.container", "kernel", True, True),
    ("api.error_contracts", "api", True, True),
    ("identity.dev_context", "api", True, True),
    ("policy.opa_adapter", "policy", True, True),
    ("policy.catalog", "policy", True, True),
    ("event.intake", "api", True, True),
    ("event.reaction_router", "api", True, False),
    ("command_bus", "api", True, False),
    ("outbox", "api", True, False),
    ("inbox", "api", True, False),
    ("memory.lexical", "memory", True, True),
    ("memory.semantic_pgvector", "memory", True, False),
    ("memory.semantic_turbovec_optional", "memory", False, False),
    ("memory.graph_postgres", "graph", True, False),
    ("memory.graphiti_optional", "graph", False, False),
    ("evidence.vault", "evidence", True, False),
    ("retrieval.router", "retrieval", True, False),
    ("attention.controller", "api", True, False),
    ("working_memory", "memory", True, False),
    ("reasoning.deterministic", "reasoning", True, True),
    ("model_gateway.optional", "reasoning", False, False),
    ("planning.deterministic", "planning", True, True),
    ("execution.orchestrator", "execution", True, False),
    ("workflow.local_engine", "workflow", True, False),
    ("cycles.sleep_consolidation", "workflow", True, False),
    ("autonomy.governor", "autonomy", True, False),
    ("risk.engine", "risk", True, False),
    ("approval.control_plane", "approval", True, False),
    ("module.registry", "module", True, False),
    ("module.developer_kit", "module", True, False),
    ("sandbox.control_plane", "sandbox", True, False),
    ("mcp.optional", "mcp", False, False),
    ("visual.projection", "visual", True, False),
    ("replay.regression", "regression", True, False),
    ("scenarios.golden_path", "scenario", True, True),
    ("sdk.python", "sdk", True, True),
    ("cli.aionctl", "cli", True, True),
    ("ci.quality_gates", "release", True, True),
    ("runtime_config.control_plane", "release", True, True),
    ("runtime_config.feature_overrides", "release", True, False),
)


class FeatureRegistryService:
    """Manage the generic AION v0.1 feature registry."""

    def __init__(
        self,
        repository: VersioningRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def seed_defaults(self, scope: list[str], *, dry_run: bool = True) -> dict[str, Any]:
        """Seed default generic feature registry entries."""
        self._authorize(
            "version.feature.create",
            scope,
            context={"dry_run": dry_run, "seed_defaults": True},
        )
        defaults = default_feature_entries(scope)
        if dry_run:
            return {
                "dry_run": True,
                "feature_count": len(defaults),
                "feature_keys": [entry.feature_key for entry in defaults],
            }
        persisted = [self.create_feature(entry) for entry in defaults]
        return {
            "dry_run": False,
            "feature_count": len(persisted),
            "feature_keys": [entry.feature_key for entry in persisted],
        }

    def list_features(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> list[FeatureRegistryEntry]:
        """List stored feature entries or defaults when none are stored."""
        self._authorize("version.feature.read", scope, context={"status": status})
        features = self._repository.list_features(status=status, category=category)
        if not features:
            features = default_feature_entries(scope)
        if status:
            features = [feature for feature in features if feature.status == status]
        if category:
            features = [feature for feature in features if feature.category == category]
        return features

    def get_feature(self, feature_key: str, scope: list[str]) -> FeatureRegistryEntry | None:
        """Return one feature entry by key."""
        self._authorize("version.feature.read", scope, resource_id=feature_key)
        return self._repository.get_feature(feature_key)

    def create_feature(self, entry: FeatureRegistryEntry) -> FeatureRegistryEntry:
        """Create or replace a feature entry."""
        self._authorize(
            "version.feature.create",
            entry.owner_scope,
            resource_id=entry.feature_key,
            context={"feature_key": entry.feature_key},
        )
        now = datetime.now(UTC)
        saved = self._repository.save_feature(
            entry.model_copy(
                update={
                    "created_at": entry.created_at or now,
                    "updated_at": now,
                }
            )
        )
        self._emit(
            "feature_registered",
            saved.feature_id,
            saved.owner_scope,
            {"key": saved.feature_key},
        )
        return saved

    def deprecate_feature(
        self,
        feature_key: str,
        scope: list[str],
        *,
        actor_id: str | None,
        reason: str,
    ) -> FeatureRegistryEntry:
        """Mark a feature as deprecated."""
        self._authorize(
            "version.feature.deprecate",
            scope,
            actor_id=actor_id,
            resource_id=feature_key,
            context={"reason": reason},
            risk_level="medium",
        )
        entry = self._repository.get_feature(feature_key)
        if entry is None:
            for default in default_feature_entries(scope):
                if default.feature_key == feature_key:
                    entry = default
                    break
        if entry is None:
            raise AIONNotFoundException("feature_not_found")
        now = datetime.now(UTC)
        saved = self._repository.save_feature(
            entry.model_copy(
                update={
                    "status": "deprecated",
                    "deprecated_at": now,
                    "updated_at": now,
                    "metadata": {**entry.metadata, "deprecation_reason": reason},
                }
            )
        )
        self._emit(
            "feature_deprecated",
            saved.feature_id,
            saved.owner_scope,
            {"key": saved.feature_key},
        )
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
                resource_type="feature",
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

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
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
                    node_type="feature",
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=0.7,
                    payload={"owner_scope": scope, **payload},
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def default_feature_entries(scope: list[str]) -> list[FeatureRegistryEntry]:
    """Return the default v0.1 feature registry entries."""
    now = datetime.now(UTC)
    return [
        FeatureRegistryEntry(
            feature_id=f"feature-{feature_key.replace('.', '-').replace('_', '-')}",
            feature_key=feature_key,
            name=feature_key.replace(".", " ").replace("_", " ").title(),
            description=f"AION v0.1 generic feature: {feature_key}.",
            status="active",
            category=cast(FeatureCategory, category),
            default_enabled=default_enabled,
            required=required,
            owner_scope=scope,
            dependencies=[],
            metadata={"optional": not default_enabled and not required},
            created_at=now,
            updated_at=now,
            deprecated_at=None,
        )
        for feature_key, category, default_enabled, required in DEFAULT_FEATURE_SPECS
    ]
