"""Deterministic provider-neutral model gateway router."""

from datetime import UTC, datetime

from aion_brain.contracts.model_gateway import ModelGatewayRequest, ModelProfile, ModelProvider
from aion_brain.contracts.reasoning import ModelRouteDecision
from aion_brain.model_gateway.profile_registry import DETERMINISTIC_PROFILE_ID
from aion_brain.model_gateway.provider_registry import DETERMINISTIC_PROVIDER_ID


class ModelGatewayRouter:
    """Select a model profile without provider lock-in."""

    def route(
        self,
        request: ModelGatewayRequest,
        providers: list[ModelProvider],
        profiles: list[ModelProfile],
        *,
        gateway_enabled: bool = False,
    ) -> tuple[ModelRouteDecision, ModelProvider, ModelProfile]:
        """Return a deterministic route decision, provider, and profile."""
        provider_by_id = {provider.provider_id: provider for provider in providers}
        active_profiles = [
            profile
            for profile in profiles
            if profile.status == "active"
            and _provider_available(provider_by_id.get(profile.provider_id))
            and _profile_matches_request(profile, request)
        ]
        if request.preferred_profile_id:
            preferred = next(
                (
                    profile
                    for profile in active_profiles
                    if profile.model_profile_id == request.preferred_profile_id
                ),
                None,
            )
            if preferred is not None and _external_allowed(preferred, request, gateway_enabled):
                return _decision(request, provider_by_id[preferred.provider_id], preferred)

        candidates = [
            profile
            for profile in active_profiles
            if _external_allowed(profile, request, gateway_enabled)
        ]
        deterministic = next(
            (
                profile
                for profile in candidates
                if profile.model_profile_id == DETERMINISTIC_PROFILE_ID
                or profile.provider_id == DETERMINISTIC_PROVIDER_ID
            ),
            None,
        )
        if deterministic is not None:
            return _decision(request, provider_by_id[deterministic.provider_id], deterministic)

        if request.risk_level in {"high", "critical"}:
            verify = next((profile for profile in candidates if profile.mode == "verify"), None)
            if verify is not None:
                return _decision(request, provider_by_id[verify.provider_id], verify)

        if candidates:
            profile = candidates[0]
            return _decision(request, provider_by_id[profile.provider_id], profile)
        raise LookupError("model_provider_unavailable")


def _provider_available(provider: ModelProvider | None) -> bool:
    if provider is None or provider.status != "active":
        return False
    return provider.health_status != "unhealthy" or provider.provider_type == "deterministic"


def _profile_matches_request(profile: ModelProfile, request: ModelGatewayRequest) -> bool:
    return profile.mode == request.mode or profile.provider_id == DETERMINISTIC_PROVIDER_ID


def _external_allowed(
    profile: ModelProfile,
    request: ModelGatewayRequest,
    gateway_enabled: bool,
) -> bool:
    if profile.privacy_level == "local" or profile.provider_id == DETERMINISTIC_PROVIDER_ID:
        return True
    return request.allow_external and gateway_enabled


def _decision(
    request: ModelGatewayRequest,
    provider: ModelProvider,
    profile: ModelProfile,
) -> tuple[ModelRouteDecision, ModelProvider, ModelProfile]:
    return (
        ModelRouteDecision(
            route_id=f"route-{request.request_id}",
            trace_id=request.trace_id,
            reasoning_id=request.reasoning_id,
            selected_provider=provider.provider_id,
            selected_model=profile.model_name,
            mode=request.mode,
            reason="deterministic_model_gateway_route",
            fallback_providers=[DETERMINISTIC_PROVIDER_ID]
            if provider.provider_id != DETERMINISTIC_PROVIDER_ID
            else [],
            privacy_level=profile.privacy_level,
            risk_level=request.risk_level,
            estimated_cost=0.0,
            estimated_latency_ms=0 if provider.provider_type == "deterministic" else None,
            created_at=datetime.now(UTC),
        ),
        provider,
        profile,
    )
