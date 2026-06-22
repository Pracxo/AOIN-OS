"""Model gateway resilience integration tests."""

from __future__ import annotations

from aion_brain.resilience.circuit_breakers import CircuitBreakerService
from tests.model_gateway_fakes import (
    external_profile,
    external_provider,
    gateway_request,
    model_gateway_service,
)
from tests.resilience_fakes import AllowPolicy, circuit_breaker, repository


def test_model_gateway_respects_open_circuit_breaker_for_external_profile() -> None:
    service, repo, _, _ = model_gateway_service(gateway_enabled=True)
    breaker_service = CircuitBreakerService(repository(), AllowPolicy())
    breaker_service.create_breaker(
        circuit_breaker("model_gateway").model_copy(
            update={
                "target_type": "model_gateway",
                "failure_count": 2,
                "status": "open",
            }
        )
    )
    service.set_circuit_breaker_service(breaker_service)
    repo.save_provider(external_provider())
    repo.save_profile(
        external_profile().model_copy(
            update={
                "cost_per_1k_input_tokens": 0.0,
                "cost_per_1k_output_tokens": 0.0,
            }
        )
    )
    request = gateway_request().model_copy(
        update={
            "preferred_profile_id": "external-profile",
            "allow_external": True,
            "metadata": {"permissions": ["model.external.use"]},
        }
    )

    response = service.complete(request)

    assert response.status == "provider_unavailable"
    assert response.output["reason"] == "circuit_breaker_open"
