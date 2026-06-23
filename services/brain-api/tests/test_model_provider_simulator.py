"""Model provider simulator tests."""

from __future__ import annotations

from tests.model_provider_hardening_helpers import services, simulation_request


def test_model_provider_simulator_creates_deterministic_synthetic_response() -> None:
    simulator = services()["simulator"]

    result = simulator.simulate(simulation_request())  # type: ignore[attr-defined]
    again = simulator.simulate(simulation_request())  # type: ignore[attr-defined]

    assert result.redacted_simulated_response["synthetic"] is True
    assert result.redacted_simulated_response["generated_by"] == "aion.model_provider_simulator"
    assert result.simulated_response_hash == again.simulated_response_hash
    assert result.external_calls_made is False
    assert result.credentials_used is False
    assert result.model_invoked is False


def test_model_provider_simulator_blocks_tool_intent() -> None:
    simulator = services()["simulator"]

    result = simulator.simulate(  # type: ignore[attr-defined]
        simulation_request(simulated_request={"tool_call": {"name": "run"}})
    )

    assert result.tool_intent_status == "blocked"
    assert result.status == "blocked"
    assert result.model_invoked is False
