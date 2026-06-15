"""Model provider registry with policy-gated access."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.model_gateway import ModelProvider, ModelProviderHealth
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.model_gateway.repository import ModelGatewayRepository
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher

DETERMINISTIC_PROVIDER_ID = "deterministic"


def deterministic_provider() -> ModelProvider:
    """Return the built-in local deterministic provider."""
    return ModelProvider(
        provider_id=DETERMINISTIC_PROVIDER_ID,
        provider_type="deterministic",
        display_name="AION Deterministic Provider",
        status="active",
        endpoint_ref=None,
        config={"local": True},
        health_status="healthy",
    )


class ModelProviderRegistry:
    """Policy-gated registry for provider boundaries."""

    def __init__(
        self,
        repository: ModelGatewayRepository,
        policy_adapter: PolicyAdapter | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._local_providers: dict[str, ModelProvider] = {}

    def ensure_defaults(self) -> None:
        """Ensure the deterministic provider exists."""
        try:
            if self._repository.get_provider(DETERMINISTIC_PROVIDER_ID) is None:
                self._repository.save_provider(deterministic_provider())
        except Exception:
            self._local_providers[DETERMINISTIC_PROVIDER_ID] = deterministic_provider()

    def register_provider(
        self,
        provider: ModelProvider,
        actor_context: ActorContext | None = None,
    ) -> ModelProvider:
        """Register a provider after policy authorization."""
        self._authorize("model.provider.register", provider.provider_id, actor_context)
        try:
            stored = self._repository.save_provider(provider)
        except Exception:
            self._local_providers[provider.provider_id] = provider
            stored = provider
        return stored

    def get_provider(
        self,
        provider_id: str,
        actor_context: ActorContext | None = None,
    ) -> ModelProvider | None:
        """Return a provider by ID."""
        self._authorize("model.provider.read", provider_id, actor_context)
        try:
            provider = self._repository.get_provider(provider_id)
        except Exception:
            provider = None
        return provider or self._local_providers.get(provider_id)

    def list_providers(
        self,
        status: str | None = None,
        actor_context: ActorContext | None = None,
    ) -> list[ModelProvider]:
        """List providers."""
        self._authorize("model.provider.read", None, actor_context)
        try:
            providers = self._repository.list_providers(status)
        except Exception:
            providers = []
        local = [
            provider
            for provider in self._local_providers.values()
            if status is None or provider.status == status
        ]
        by_id = {provider.provider_id: provider for provider in [*providers, *local]}
        return list(by_id.values())

    def disable_provider(
        self,
        provider_id: str,
        reason: str | None = None,
        actor_context: ActorContext | None = None,
    ) -> ModelProvider:
        """Disable a provider."""
        self._authorize("model.provider.disable", provider_id, actor_context)
        provider = self._lookup_provider(provider_id)
        if provider is None:
            raise KeyError(provider_id)
        metadata = {**provider.config, "disabled_reason": reason} if reason else provider.config
        disabled = provider.model_copy(
            update={"status": "disabled", "config": metadata, "updated_at": datetime.now(UTC)}
        )
        try:
            return self._repository.save_provider(disabled)
        except Exception:
            self._local_providers[provider_id] = disabled
            return disabled

    def health_check(
        self,
        provider_id: str,
        actor_context: ActorContext | None = None,
    ) -> ModelProviderHealth:
        """Run a local, non-network provider health check."""
        self._authorize("model.provider.health_check", provider_id, actor_context)
        provider = self._lookup_provider(provider_id)
        if provider is None:
            return ModelProviderHealth(
                provider_id=provider_id,
                status="unhealthy",
                latency_ms=None,
                details={"reason": "provider_not_found"},
                checked_at=datetime.now(UTC),
            )
        status = "healthy" if provider.provider_type == "deterministic" else provider.health_status
        health = ModelProviderHealth(
            provider_id=provider_id,
            status=status,
            latency_ms=0 if provider.provider_type == "deterministic" else None,
            details={"network_checked": False},
            checked_at=datetime.now(UTC),
        )
        updated = provider.model_copy(
            update={
                "health_status": health.status,
                "last_health_check_at": health.checked_at,
                "updated_at": health.checked_at,
            }
        )
        try:
            self._repository.save_provider(updated)
        except Exception:
            self._local_providers[provider_id] = updated
        return health

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
                    resource_type="model_provider",
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

    def _lookup_provider(self, provider_id: str) -> ModelProvider | None:
        try:
            provider = self._repository.get_provider(provider_id)
        except Exception:
            provider = None
        return provider or self._local_providers.get(provider_id)
