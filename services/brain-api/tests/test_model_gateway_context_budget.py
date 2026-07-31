from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.model_gateway import ModelGatewayContextBudget, ModelGatewayContextUsage
from aion_brain.model_gateway.context_budget import evaluate_context_budget


def test_context_budget_allows_within_limits_and_rejects_one_over_limit() -> None:
    budget = ModelGatewayContextBudget(maximum_messages_per_request=1)
    ok = evaluate_context_budget(
        decision_id="context-ok",
        budget=budget,
        usage=ModelGatewayContextUsage(
            message_count=1,
            context_item_count=0,
            prompt_utf8_bytes=1,
            context_utf8_bytes=0,
            response_byte_limit=1,
            structured_schema_bytes=0,
            structured_schema_depth=0,
        ),
        created_at=datetime(2026, 7, 31, tzinfo=UTC),
    )
    blocked_usage = ModelGatewayContextUsage(
        message_count=2,
        context_item_count=0,
        prompt_utf8_bytes=1,
        context_utf8_bytes=0,
        response_byte_limit=1,
        structured_schema_bytes=0,
        structured_schema_depth=0,
    )
    blocked = evaluate_context_budget(
        decision_id="context-blocked",
        budget=budget,
        usage=blocked_usage,
        created_at=datetime(2026, 7, 31, tzinfo=UTC),
    )
    assert ok.allowed is True
    assert blocked.allowed is False
    assert "message_count_exceeded" in blocked.reason_codes
