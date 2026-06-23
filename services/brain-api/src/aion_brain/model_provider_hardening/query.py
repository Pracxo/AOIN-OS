"""Model provider hardening aggregate query service."""

from __future__ import annotations

from aion_brain.contracts.model_provider_hardening import (
    ProviderHardeningQuery,
    ProviderHardeningQueryResult,
)
from aion_brain.model_provider_hardening.policy import authorize_model_provider_action
from aion_brain.model_provider_hardening.repository import ModelProviderHardeningRepository


class ProviderHardeningQueryService:
    """Aggregate provider readiness, previews, simulations, and blockers."""

    def __init__(
        self,
        repository: ModelProviderHardeningRepository,
        policy_adapter: object,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, request: ProviderHardeningQuery) -> ProviderHardeningQueryResult:
        """Return aggregate provider hardening records."""

        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.query",
            request.scope,
            resource_type="model_provider_hardening",
            risk_level="low",
            context=request.model_dump(mode="json"),
        )
        profiles = [
            item
            for item in self._repository.list_profiles(
                provider_key=request.provider_key,
                status=request.status,
                risk_level=request.risk_level,
                limit=request.limit,
            )
            if _in_scope(item.owner_scope, request.scope)
        ]
        previews = [
            item
            for item in self._repository.list_egress_previews(
                provider_key=request.provider_key,
                status=request.status,
                limit=request.limit,
            )
            if _in_scope(item.owner_scope, request.scope)
        ]
        simulations = [
            item
            for item in self._repository.list_simulations(
                provider_key=request.provider_key,
                status=request.status,
                limit=request.limit,
            )
            if _in_scope(item.owner_scope, request.scope)
        ]
        readiness = [
            item
            for item in self._repository.list_readiness(
                provider_key=request.provider_key,
                status=request.status,
                limit=request.limit,
            )
            if _in_scope(item.owner_scope, request.scope)
        ]
        blockers = self._repository.list_blockers(
            provider_key=request.provider_key,
            status=request.status,
            limit=request.limit,
        )
        total_count = (
            len(profiles)
            + len(previews)
            + len(simulations)
            + len(readiness)
            + len(blockers)
        )
        constraints = [
            "metadata_only",
            "no_external_calls",
            "no_credentials",
            "no_model_invocation",
        ]
        return ProviderHardeningQueryResult(
            profiles=profiles,
            egress_previews=previews,
            simulations=simulations,
            readiness_assessments=readiness,
            blockers=blockers,
            total_count=total_count,
            constraints=constraints,
            metadata={
                "external_model_calls_enabled": False,
                "model_provider_credentials_enabled": False,
                "provider_activation_enabled": False,
            },
        )


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    requested = set(requested_scope or [])
    return not requested or bool(set(owner_scope) & requested)


__all__ = ["ProviderHardeningQueryService"]
