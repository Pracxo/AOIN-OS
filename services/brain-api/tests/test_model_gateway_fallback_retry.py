from __future__ import annotations

import pytest

from aion_brain.contracts.model_gateway import ModelRetryPlan
from tests.model_gateway_aion233_test_support import gateway_flow


def test_fallback_and_retry_are_planned_only() -> None:
    flow = gateway_flow()
    assert flow.fallback.planning_only is True
    assert flow.fallback.automatic_fallback_execution is False
    assert flow.retry.planning_only is True
    assert flow.retry.automatic_retry_execution is False
    assert flow.retry.planned_attempts == 2


def test_retry_over_limit_is_rejected() -> None:
    flow = gateway_flow()
    payload = flow.retry.model_dump(mode="python")
    payload["planned_attempts"] = 3
    payload["deterministic_delay_milliseconds"] = (50, 100, 150)
    payload.pop("plan_fingerprint", None)
    with pytest.raises(ValueError):
        ModelRetryPlan.model_validate(payload)
