from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.model_gateway import ModelGatewayTokenBudget, ModelGatewayTokenUsage
from aion_brain.model_gateway.context_budget import evaluate_token_budget


def test_token_budget_uses_estimates_and_fails_closed_over_limit() -> None:
    budget = ModelGatewayTokenBudget(maximum_input_tokens_per_request=3)
    ok = evaluate_token_budget(
        decision_id="token-ok",
        budget=budget,
        usage=ModelGatewayTokenUsage(
            estimated_input_tokens=3,
            requested_output_tokens=1,
            estimated_session_tokens_after_request=4,
        ),
        created_at=datetime(2026, 7, 31, tzinfo=UTC),
    )
    blocked_usage = ModelGatewayTokenUsage(
        estimated_input_tokens=4,
        requested_output_tokens=1,
        estimated_session_tokens_after_request=5,
    )
    blocked = evaluate_token_budget(
        decision_id="token-blocked",
        budget=budget,
        usage=blocked_usage,
        created_at=datetime(2026, 7, 31, tzinfo=UTC),
    )
    assert ok.allowed is True
    assert blocked.allowed is False
    assert "input_tokens_exceeded" in blocked.reason_codes
