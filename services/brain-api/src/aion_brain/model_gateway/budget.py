"""Deterministic model gateway budget guard."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.contracts.model_gateway import (
    ModelBudgetRecord,
    ModelBudgetStatus,
    ModelGatewayRequest,
    ModelProfile,
    ModelUsageRecord,
)
from aion_brain.contracts.reasoning import PromptPacket
from aion_brain.model_gateway.repository import ModelGatewayRepository


class ModelBudgetGuard:
    """Estimate tokens and enforce local budget records."""

    def __init__(
        self,
        repository: ModelGatewayRepository,
        *,
        default_daily_budget: float = 0.0,
        default_currency: str = "USD",
    ) -> None:
        self._repository = repository
        self._default_daily_budget = default_daily_budget
        self._default_currency = default_currency

    def estimate_tokens(self, text: str) -> int:
        """Estimate tokens with a deterministic chars / 4 heuristic."""
        if not text:
            return 0
        return max(1, (len(text) + 3) // 4)

    def estimate_prompt_tokens(self, prompt: PromptPacket) -> int:
        """Estimate prompt packet token usage."""
        return self.estimate_tokens(prompt.model_dump_json())

    def estimate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        profile: ModelProfile,
    ) -> float:
        """Estimate request cost from profile pricing."""
        input_rate = profile.cost_per_1k_input_tokens or 0.0
        output_rate = profile.cost_per_1k_output_tokens or 0.0
        return (input_tokens / 1000.0 * input_rate) + (output_tokens / 1000.0 * output_rate)

    def authorize_budget(
        self,
        request: ModelGatewayRequest,
        profile: ModelProfile,
    ) -> ModelBudgetRecord | None:
        """Return an authorizing budget record or None when blocked."""
        input_tokens = self.estimate_prompt_tokens(request.prompt)
        cost = self.estimate_cost(input_tokens, profile.max_output_tokens, profile)
        if profile.privacy_level == "local" or cost == 0.0:
            return _synthetic_budget(request, status="active", limit=0.0, used=0.0)

        budgets = self._repository.list_budgets(
            workspace_id=request.workspace_id,
            actor_id=request.actor_id,
            status="active",
        )
        for budget in budgets:
            if budget.limit_amount - budget.used_amount >= cost:
                return budget
        if self._default_daily_budget > 0 and cost <= self._default_daily_budget:
            return _synthetic_budget(
                request,
                status="active",
                limit=self._default_daily_budget,
                used=0.0,
                currency=self._default_currency,
            )
        return None

    def record_usage(self, usage: ModelUsageRecord) -> ModelUsageRecord:
        """Persist usage locally."""
        return self._repository.save_usage(usage)


def _synthetic_budget(
    request: ModelGatewayRequest,
    *,
    status: str,
    limit: float,
    used: float,
    currency: str = "USD",
) -> ModelBudgetRecord:
    return ModelBudgetRecord(
        budget_id=f"budget-{request.request_id}-{uuid4().hex[:8]}",
        workspace_id=request.workspace_id,
        actor_id=request.actor_id,
        scope=request.scope,
        budget_type="session",
        limit_amount=limit,
        used_amount=used,
        currency=currency,
        status=cast(ModelBudgetStatus, status),
        resets_at=None,
        metadata={"synthetic": True},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
