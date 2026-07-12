from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.production_auth import (
    ProductionAuthCoreConfig,
    ProductionAuthPolicyRequest,
)
from aion_brain.production_auth.policy import ProductionAuthPolicyEvaluator


def test_production_auth_policy_evaluator_is_deterministic_and_fail_closed() -> None:
    evaluator = ProductionAuthPolicyEvaluator(
        clock=lambda: datetime(2026, 7, 12, tzinfo=UTC),
        id_factory=lambda: "decision-fixed",
    )
    request = ProductionAuthPolicyRequest(
        request_id="request-fixed",
        requested_operation="future_callback",
        owner_scope=["workspace:main"],
    )

    decision = evaluator.evaluate(request, ProductionAuthCoreConfig())

    assert decision.decision_id == "decision-fixed"
    assert decision.created_at == datetime(2026, 7, 12, tzinfo=UTC)
    assert decision.outcome == "blocked"
    assert decision.runtime_effect is False
    assert decision.metadata["owner_scope"] == ["workspace:main"]


def test_production_auth_policy_request_rejects_unsafe_metadata() -> None:
    with pytest.raises(ValidationError):
        ProductionAuthPolicyRequest(
            request_id="request-unsafe",
            requested_operation="future_status",
            metadata={"session_token": "demo"},
        )
