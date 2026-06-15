"""Model usage ledger service."""

from aion_brain.contracts.model_gateway import ModelUsageRecord
from aion_brain.model_gateway.repository import ModelGatewayRepository


class ModelUsageLedger:
    """Small service wrapper around model usage persistence."""

    def __init__(self, repository: ModelGatewayRepository) -> None:
        self._repository = repository

    def record_usage(self, usage: ModelUsageRecord) -> ModelUsageRecord:
        """Persist a usage record."""
        return self._repository.save_usage(usage)

    def list_usage(
        self,
        *,
        trace_id: str | None = None,
        reasoning_id: str | None = None,
        provider_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> list[ModelUsageRecord]:
        """List usage records."""
        return self._repository.list_usage(
            trace_id=trace_id,
            reasoning_id=reasoning_id,
            provider_id=provider_id,
            workspace_id=workspace_id,
            limit=limit,
        )
