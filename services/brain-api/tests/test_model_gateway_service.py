"""Model gateway service tests."""

from tests.model_gateway_fakes import (
    DenyPolicy,
    FailingAdapter,
    external_profile,
    external_provider,
    gateway_request,
    model_gateway_service,
)


def test_gateway_service_calls_policy_for_gateway_completion() -> None:
    service, _, policy, _ = model_gateway_service()
    response = service.complete(gateway_request())
    assert response.status == "completed"
    assert "model.gateway.complete" in [request.action_type for request in policy.requests]


def test_policy_deny_blocks_gateway_completion() -> None:
    service, _, _, _ = model_gateway_service(policy=DenyPolicy("model.gateway.complete"))
    response = service.complete(gateway_request())
    assert response.status == "blocked_by_policy"
    assert response.usage.status == "blocked"


def test_gateway_service_blocks_redacted_prompt_when_required() -> None:
    service, _, _, _ = model_gateway_service()
    response = service.complete(gateway_request("api_key=secret-value-123456"))
    assert response.status == "blocked_by_redaction"
    assert response.redaction is not None
    assert response.redaction.blocked is True


def test_gateway_service_blocks_budget_overrun() -> None:
    service, repo, _, _ = model_gateway_service(gateway_enabled=True)
    repo.save_provider(external_provider())
    repo.save_profile(external_profile())
    request = gateway_request().model_copy(
        update={
            "preferred_profile_id": "external-profile",
            "allow_external": True,
            "metadata": {"permissions": ["model.external.use"]},
        }
    )
    response = service.complete(request)
    assert response.status == "blocked_by_budget"


def test_gateway_service_records_usage() -> None:
    service, repo, _, _ = model_gateway_service()
    response = service.complete(gateway_request())
    usage = repo.list_usage(reasoning_id="reasoning-1")
    assert response.usage in usage


def test_gateway_service_uses_deterministic_fallback_on_provider_failure() -> None:
    service, repo, _, _ = model_gateway_service(
        adapters={"litellm_http": FailingAdapter()},
        gateway_enabled=True,
    )
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
    assert response.status == "fallback_used"
    assert response.model_call.provider == "deterministic"
