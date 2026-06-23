"""Provider hardening blocker service."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.model_provider_hardening import (
    ModelProviderBlocker,
    ModelProviderBlockerDismissRequest,
)
from aion_brain.model_provider_hardening.policy import authorize_model_provider_action
from aion_brain.model_provider_hardening.repository import ModelProviderHardeningRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ModelProviderBlockerService:
    """Read and dismiss provider blockers without enabling providers."""

    def __init__(
        self,
        repository: ModelProviderHardeningRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def list_blockers(
        self,
        scope: list[str],
        *,
        provider_key: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ModelProviderBlocker]:
        """List blockers after policy authorization."""

        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.blocker.read",
            scope,
            resource_type="model_provider_blocker",
            risk_level="low",
        )
        return self._repository.list_blockers(
            provider_key=provider_key,
            status=status,
            severity=severity,
            limit=limit,
        )

    def dismiss_blocker(
        self,
        provider_blocker_id: str,
        scope: list[str],
        request: ModelProviderBlockerDismissRequest,
    ) -> ModelProviderBlocker:
        """Dismiss a blocker without enabling a provider."""

        authorize_model_provider_action(
            self._policy_adapter,
            "model_provider.blocker.update",
            scope,
            actor_id=request.actor_id,
            resource_type="model_provider_blocker",
            resource_id=provider_blocker_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        blocker = self._repository.get_blocker(provider_blocker_id)
        if blocker is None:
            raise AIONNotFoundException("model_provider_blocker_not_found")
        saved = self._repository.save_blocker(
            blocker.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {
                        **blocker.metadata,
                        **request.metadata,
                        "dismiss_reason": request.reason,
                        "provider_enabled": False,
                    },
                }
            )
        )
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="model_provider_blocker_dismissed",
            node_type="model_provider_blocker",
            node_id=saved.provider_blocker_id,
            scope=scope,
            intensity=0.3,
            payload={"provider_enabled": False},
        )
        return saved


__all__ = ["ModelProviderBlockerService"]
