from __future__ import annotations

import pytest

from aion_brain.contracts.model_gateway import ModelGatewayCircuitBreakerStatus
from aion_brain.model_gateway.circuit_breaker import InMemoryModelCircuitBreakerRepository
from tests.model_gateway_aion233_test_support import NOW


def test_circuit_open_blocks_routing_and_half_open_remains_simulation_only() -> None:
    repo = InMemoryModelCircuitBreakerRepository()
    open_state = repo.transition(
        record_id="circuit-open",
        model_id="reference-text-sim-v1",
        next_status=ModelGatewayCircuitBreakerStatus.open,
        reason_code="fixture_failure",
        deterministic_fixture_failure=True,
        created_at=NOW,
    )
    half_open = repo.transition(
        record_id="circuit-half-open",
        model_id="reference-text-sim-v1",
        next_status=ModelGatewayCircuitBreakerStatus.half_open,
        reason_code="operator_review",
        deterministic_fixture_failure=False,
        created_at=NOW,
    )
    assert open_state.routing_allowed is False
    assert half_open.routing_allowed is True
    assert half_open.deterministic_reference_simulation_only is True


def test_circuit_bypass_is_rejected() -> None:
    state = InMemoryModelCircuitBreakerRepository().transition(
        record_id="circuit-open",
        model_id="reference-text-sim-v1",
        next_status=ModelGatewayCircuitBreakerStatus.open,
        reason_code="fixture_failure",
        deterministic_fixture_failure=True,
        created_at=NOW,
    )
    payload = state.model_dump(mode="python")
    payload["routing_allowed"] = True
    payload.pop("state_fingerprint", None)
    with pytest.raises(ValueError):
        type(state).model_validate(payload)
