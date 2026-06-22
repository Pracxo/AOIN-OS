"""Module mock profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.module_mock_runtime import (
    ModuleMockProfile,
    ModuleMockProfileCreateRequest,
    ModuleMockProfileSeedRequest,
)
from aion_brain.module_mock_runtime.policy import authorize_module_mock_action
from aion_brain.module_mock_runtime.repository import ModuleMockRuntimeRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ModuleMockProfileService:
    """Create and list deterministic metadata-only mock profiles."""

    def __init__(
        self,
        repository: ModuleMockRuntimeRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_profile(self, request: ModuleMockProfileCreateRequest) -> ModuleMockProfile:
        """Persist one active mock profile."""

        if not self._settings.module_mock_profiles_enabled:
            raise RuntimeError("module_mock_profiles_disabled")
        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.profile.create",
            request.owner_scope,
            actor_id=request.created_by,
            resource_type="module_mock_profile",
            risk_level="medium",
            context={"profile_key": request.profile_key, "metadata_only": True},
        )
        now = datetime.now(UTC)
        profile = ModuleMockProfile(
            mock_profile_id=request.mock_profile_id or f"module-mock-profile-{uuid4().hex}",
            profile_key=request.profile_key,
            name=request.name,
            description=request.description,
            status="active",
            profile_type=request.profile_type,
            owner_scope=request.owner_scope,
            supported_capability_types=request.supported_capability_types,
            supported_capability_keys=request.supported_capability_keys,
            input_schema_hints=request.input_schema_hints,
            output_schema_hints=request.output_schema_hints,
            simulation_rules=request.simulation_rules,
            constraints=[*request.constraints, "dry_run_only", "synthetic_output_only"],
            metadata={**request.metadata, "metadata_only": True},
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_profile(profile)
        self._emit("module_mock_profile_created", saved.mock_profile_id, saved.owner_scope, 0.4)
        return saved

    def seed_defaults(self, request: ModuleMockProfileSeedRequest) -> dict[str, Any]:
        """Return or persist the default generic mock profiles."""

        scope = request.scope or ["workspace:main"]
        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.profile.create",
            scope,
            actor_id=request.created_by,
            resource_type="module_mock_profile_seed",
            risk_level="medium",
            context={"dry_run": request.dry_run, "metadata_only": True},
        )
        defaults = [_default_profile_payload(scope, request.created_by, item) for item in _DEFAULTS]
        if request.dry_run:
            return {
                "seeded": False,
                "dry_run": True,
                "profile_count": len(defaults),
                "profiles": defaults,
                "constraints": ["no_source_mutation", "no_activation", "no_execution"],
            }
        profiles = [
            self.create_profile(ModuleMockProfileCreateRequest.model_validate(item))
            for item in defaults
        ]
        return {
            "seeded": True,
            "dry_run": False,
            "profile_count": len(profiles),
            "profiles": [item.model_dump(mode="json") for item in profiles],
            "constraints": ["no_activation", "no_execution"],
        }

    def get_profile(self, mock_profile_id: str, scope: list[str]) -> ModuleMockProfile:
        """Return a profile inside scope."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.profile.read",
            scope,
            resource_type="module_mock_profile",
            resource_id=mock_profile_id,
            risk_level="low",
        )
        profile = self._repository.get_profile(mock_profile_id)
        if profile is None or not _in_scope(profile.owner_scope, scope):
            raise AIONNotFoundException("module_mock_profile_not_found")
        return profile

    def list_profiles(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMockProfile]:
        """List profiles inside scope."""

        authorize_module_mock_action(
            self._policy_adapter,
            "module_mock.profile.read",
            scope,
            resource_type="module_mock_profile",
            risk_level="low",
        )
        return [
            item
            for item in self._repository.list_profiles(
                status=status,
                profile_type=profile_type,
                limit=limit,
            )
            if _in_scope(item.owner_scope, scope)
        ]

    def _emit(self, event_type: str, node_id: str, scope: list[str], intensity: float) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="module_mock_profile",
            node_id=node_id,
            scope=scope,
            intensity=intensity,
            payload={"metadata_only": True, "dry_run_only": True},
        )


_DEFAULTS = (
    ("generic.schema_echo", "Generic Schema Echo", "schema_echo"),
    ("generic.shape_simulation", "Generic Shape Simulation", "shape_simulation"),
    ("generic.knowledge_stub", "Generic Knowledge Stub", "knowledge_stub"),
    ("generic.summary_stub", "Generic Summary Stub", "generic"),
    ("generic.grounding_stub", "Generic Grounding Stub", "grounding_stub"),
    ("generic.explanation_stub", "Generic Explanation Stub", "explanation_stub"),
    ("generic.answer_stub", "Generic Answer Stub", "answer_stub"),
)


def _default_profile_payload(
    scope: list[str],
    created_by: str | None,
    item: tuple[str, str, str],
) -> dict[str, Any]:
    key, name, profile_type = item
    return {
        "mock_profile_id": f"module-mock-profile-{key.replace('.', '-')}",
        "profile_key": key,
        "name": name,
        "description": "Deterministic synthetic profile for generic module dry-runs.",
        "profile_type": profile_type,
        "owner_scope": scope,
        "supported_capability_types": ["generic"],
        "supported_capability_keys": ["generic.knowledge.retrieve"],
        "input_schema_hints": {"type": "object"},
        "output_schema_hints": {"type": "object", "synthetic": True},
        "simulation_rules": [{"rule": "metadata_shape_only", "synthetic": True}],
        "constraints": ["dry_run_only", "no_external_calls", "no_code_loading"],
        "metadata": {"default_profile": True, "activation_allowed": False},
        "created_by": created_by,
    }


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    requested = set(requested_scope or [])
    return not requested or bool(set(owner_scope) & requested)


__all__ = ["ModuleMockProfileService"]
