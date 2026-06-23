"""Model provider profile service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderProfile,
    ModelProviderProfileCreateRequest,
    ModelProviderProfileSeedRequest,
)
from aion_brain.model_provider_hardening.policy import authorize_model_provider_action
from aion_brain.model_provider_hardening.repository import ModelProviderHardeningRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ModelProviderProfileService:
    """Create and list metadata-only provider profiles."""

    def __init__(
        self,
        repository: ModelProviderHardeningRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def create_profile(self, request: ModelProviderProfileCreateRequest) -> ModelProviderProfile:
        """Persist provider readiness metadata only."""

        if not self._settings.model_provider_profiles_enabled:
            raise RuntimeError("model_provider_profiles_disabled")
        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.profile.create",
            request.owner_scope,
            actor_id=request.created_by,
            resource_type="model_provider_profile",
            risk_level="medium",
            context={
                "provider_key": request.provider_key,
                "external_calls_allowed": request.external_calls_allowed,
                "credentials_required": request.credentials_required,
            },
        )
        now = datetime.now(UTC)
        profile = ModelProviderProfile(
            provider_profile_id=(
                request.provider_profile_id or f"model-provider-profile-{uuid4().hex}"
            ),
            provider_key=request.provider_key,
            name=request.name,
            description=request.description,
            status="proposed",
            provider_type=request.provider_type,
            owner_scope=request.owner_scope,
            supported_model_families=request.supported_model_families,
            supported_modes=request.supported_modes or ["dry_run"],
            declared_capabilities=request.declared_capabilities,
            required_settings=[
                *request.required_settings,
                "external_model_calls_enabled=false",
                "model_provider_credentials_enabled=false",
            ],
            required_policy_actions=request.required_policy_actions,
            egress_requirements=request.egress_requirements,
            output_governance_requirements=request.output_governance_requirements,
            grounding_requirements=request.grounding_requirements,
            tool_use_policy={
                **request.tool_use_policy,
                "tool_execution_allowed": False,
            },
            risk_level=request.risk_level,
            external_calls_allowed=False,
            credentials_required=request.credentials_required,
            metadata={
                **request.metadata,
                "provider_activation_enabled": False,
                "metadata_only": True,
            },
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_profile(profile)
        self._emit("model_provider_profile_created", saved.provider_profile_id, saved.owner_scope)
        return saved

    def seed_default_profiles(self, request: ModelProviderProfileSeedRequest) -> dict[str, Any]:
        """Seed or preview canonical safe provider-hardening profiles."""

        scope = request.scope or ["workspace:main"]
        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.profile.create",
            scope,
            actor_id=request.created_by,
            resource_type="model_provider_profile_seed",
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
                "constraints": ["metadata_only", "no_provider_activation", "no_external_calls"],
            }
        profiles = [
            self.create_profile(ModelProviderProfileCreateRequest.model_validate(item))
            for item in defaults
        ]
        return {
            "seeded": True,
            "dry_run": False,
            "profile_count": len(profiles),
            "profiles": [item.model_dump(mode="json") for item in profiles],
            "constraints": ["metadata_only", "no_provider_activation", "no_external_calls"],
        }

    def get_profile(self, provider_profile_id: str, scope: list[str]) -> ModelProviderProfile:
        """Return one provider profile in scope."""

        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.profile.read",
            scope,
            resource_type="model_provider_profile",
            resource_id=provider_profile_id,
            risk_level="low",
        )
        profile = self._repository.get_profile(provider_profile_id)
        if profile is None or not _in_scope(profile.owner_scope, scope):
            raise AIONNotFoundException("model_provider_profile_not_found")
        return profile

    def list_profiles(
        self,
        scope: list[str],
        *,
        provider_key: str | None = None,
        status: str | None = None,
        risk_level: str | None = None,
        limit: int = 100,
    ) -> list[ModelProviderProfile]:
        """List provider profiles in scope."""

        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.profile.read",
            scope,
            resource_type="model_provider_profile",
            risk_level="low",
        )
        return [
            item
            for item in self._repository.list_profiles(
                provider_key=provider_key,
                status=status,
                risk_level=risk_level,
                limit=limit,
            )
            if _in_scope(item.owner_scope, scope)
        ]

    def disable_profile(self, provider_profile_id: str, scope: list[str]) -> ModelProviderProfile:
        """Disable profile metadata without mutating runtime provider state."""

        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.profile.update",
            scope,
            resource_type="model_provider_profile",
            resource_id=provider_profile_id,
            risk_level="medium",
        )
        profile = self.get_profile(provider_profile_id, scope)
        return self._repository.save_profile(
            profile.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "metadata": {
                        **profile.metadata,
                        "provider_activation_enabled": False,
                    },
                }
            )
        )

    def _emit(self, event_type: str, node_id: str, scope: list[str]) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="model_provider_profile",
            node_id=node_id,
            scope=scope,
            intensity=0.45,
            payload={"metadata_only": True, "external_calls_allowed": False},
        )


_DEFAULTS = (
    ("generic.metadata_only", "Generic Metadata Only", "metadata_only"),
    ("generic.dry_run_simulator", "Generic Dry Run Simulator", "dry_run_simulator"),
    ("generic.local_stub_preview", "Generic Local Stub Preview", "local_stub"),
    (
        "generic.external_provider_preview",
        "Generic External Provider Preview",
        "external_provider_preview",
    ),
)


def _default_profile_payload(
    scope: list[str],
    created_by: str | None,
    item: tuple[str, str, str],
) -> dict[str, Any]:
    provider_key, name, provider_type = item
    return {
        "provider_profile_id": f"model-provider-profile-{provider_key.replace('.', '-')}",
        "provider_key": provider_key,
        "name": name,
        "description": "Metadata-only provider readiness profile for local dry-runs.",
        "provider_type": provider_type,
        "owner_scope": scope,
        "supported_model_families": ["generic"],
        "supported_modes": ["dry_run"],
        "declared_capabilities": ["metadata_preview", "dry_run_simulation"],
        "required_settings": [
            "external_model_calls_enabled=false",
            "model_provider_credentials_enabled=false",
        ],
        "required_policy_actions": ["model_provider.egress.preview"],
        "egress_requirements": ["prompt_summary_only", "redacted_metadata_only"],
        "output_governance_requirements": ["model_output_governance_required"],
        "grounding_requirements": ["grounding_required_for_claims"],
        "tool_use_policy": {"tool_execution_allowed": False},
        "risk_level": "medium",
        "external_calls_allowed": False,
        "credentials_required": False,
        "metadata": {"default_profile": True, "provider_activation_enabled": False},
        "created_by": created_by,
    }


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    requested = set(requested_scope or [])
    return not requested or bool(set(owner_scope) & requested)


__all__ = ["ModelProviderProfileService"]
