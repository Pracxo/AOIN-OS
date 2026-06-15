"""Model profile registry with deterministic bootstrap profile."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.model_gateway import ModelProfile
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.model_gateway.provider_registry import DETERMINISTIC_PROVIDER_ID
from aion_brain.model_gateway.repository import ModelGatewayRepository
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher

DETERMINISTIC_PROFILE_ID = "aion-deterministic-v0"
DETERMINISTIC_MODEL_NAME = "deterministic-reasoner-v0"


def deterministic_profile(
    *,
    max_input_tokens: int = 8000,
    max_output_tokens: int = 1000,
) -> ModelProfile:
    """Return the built-in deterministic profile."""
    return ModelProfile(
        model_profile_id=DETERMINISTIC_PROFILE_ID,
        provider_id=DETERMINISTIC_PROVIDER_ID,
        model_name=DETERMINISTIC_MODEL_NAME,
        mode="analyze",
        status="active",
        privacy_level="local",
        risk_level="low",
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
        cost_per_1k_input_tokens=0.0,
        cost_per_1k_output_tokens=0.0,
        latency_class="low",
        metadata={"deterministic": True},
    )


class ModelProfileRegistry:
    """Policy-gated registry for model profiles."""

    def __init__(
        self,
        repository: ModelGatewayRepository,
        policy_adapter: PolicyAdapter | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._local_profiles: dict[str, ModelProfile] = {}

    def ensure_defaults(
        self,
        *,
        max_input_tokens: int = 8000,
        max_output_tokens: int = 1000,
    ) -> None:
        """Ensure the deterministic profile exists."""
        profile = deterministic_profile(
            max_input_tokens=max_input_tokens,
            max_output_tokens=max_output_tokens,
        )
        try:
            if self._repository.get_profile(DETERMINISTIC_PROFILE_ID) is None:
                self._repository.save_profile(profile)
        except Exception:
            self._local_profiles[DETERMINISTIC_PROFILE_ID] = profile

    def register_profile(
        self,
        profile: ModelProfile,
        actor_context: ActorContext | None = None,
    ) -> ModelProfile:
        """Register a model profile."""
        self._authorize("model.profile.register", profile.model_profile_id, actor_context)
        try:
            return self._repository.save_profile(profile)
        except Exception:
            self._local_profiles[profile.model_profile_id] = profile
            return profile

    def get_profile(
        self,
        model_profile_id: str,
        actor_context: ActorContext | None = None,
    ) -> ModelProfile | None:
        """Return a profile by ID."""
        self._authorize("model.profile.read", model_profile_id, actor_context)
        try:
            profile = self._repository.get_profile(model_profile_id)
        except Exception:
            profile = None
        return profile or self._local_profiles.get(model_profile_id)

    def list_profiles(
        self,
        provider_id: str | None = None,
        mode: str | None = None,
        status: str | None = None,
        actor_context: ActorContext | None = None,
    ) -> list[ModelProfile]:
        """List model profiles."""
        self._authorize("model.profile.read", None, actor_context)
        try:
            profiles = self._repository.list_profiles(
                provider_id=provider_id,
                mode=mode,
                status=status,
            )
        except Exception:
            profiles = []
        local = [
            profile
            for profile in self._local_profiles.values()
            if (provider_id is None or profile.provider_id == provider_id)
            and (mode is None or profile.mode == mode)
            and (status is None or profile.status == status)
        ]
        by_id = {profile.model_profile_id: profile for profile in [*profiles, *local]}
        return list(by_id.values())

    def disable_profile(
        self,
        model_profile_id: str,
        reason: str | None = None,
        actor_context: ActorContext | None = None,
    ) -> ModelProfile:
        """Disable a model profile."""
        self._authorize("model.profile.disable", model_profile_id, actor_context)
        profile = self._lookup_profile(model_profile_id)
        if profile is None:
            raise KeyError(model_profile_id)
        metadata = {**profile.metadata, "disabled_reason": reason} if reason else profile.metadata
        disabled = profile.model_copy(
            update={"status": "disabled", "metadata": metadata, "updated_at": datetime.now(UTC)}
        )
        try:
            return self._repository.save_profile(disabled)
        except Exception:
            self._local_profiles[model_profile_id] = disabled
            return disabled

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        actor_context: ActorContext | None,
    ) -> None:
        if self._policy_adapter is None:
            return
        context = actor_context or ActorContext()
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(
                PolicyRequest(
                    request_id=f"{action_type}-{uuid4().hex}",
                    trace_id=context.trace_id,
                    actor_id=context.actor_id,
                    workspace_id=context.workspace_id,
                    action_type=action_type,
                    resource_type="model_profile",
                    resource_id=resource_id,
                    risk_level="low",
                    approval_present=False,
                    requested_permissions=[],
                    security_scope=context.security_scope or ["workspace:main"],
                    context={},
                ),
                context,
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _lookup_profile(self, model_profile_id: str) -> ModelProfile | None:
        try:
            profile = self._repository.get_profile(model_profile_id)
        except Exception:
            profile = None
        return profile or self._local_profiles.get(model_profile_id)
