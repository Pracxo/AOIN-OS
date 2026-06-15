"""Model gateway router tests."""

import pytest

from aion_brain.model_gateway.router import ModelGatewayRouter
from tests.model_gateway_fakes import (
    deterministic_profile_contract,
    deterministic_provider_contract,
    external_profile,
    external_provider,
    gateway_request,
)


def test_gateway_router_selects_deterministic_by_default() -> None:
    route, provider, profile = ModelGatewayRouter().route(
        gateway_request(),
        [deterministic_provider_contract(), external_provider()],
        [deterministic_profile_contract(), external_profile()],
    )
    assert provider.provider_id == "deterministic"
    assert profile.model_profile_id == "aion-deterministic-v0"
    assert route.selected_model == "deterministic-reasoner-v0"


def test_gateway_router_refuses_disabled_profiles() -> None:
    profile = deterministic_profile_contract().model_copy(update={"status": "disabled"})
    with pytest.raises(LookupError):
        ModelGatewayRouter().route(
            gateway_request(),
            [deterministic_provider_contract()],
            [profile],
        )


def test_gateway_router_refuses_external_when_not_allowed() -> None:
    request = gateway_request().model_copy(update={"preferred_profile_id": "external-profile"})
    route, provider, _ = ModelGatewayRouter().route(
        request,
        [deterministic_provider_contract(), external_provider()],
        [deterministic_profile_contract(), external_profile()],
        gateway_enabled=True,
    )
    assert provider.provider_id == "deterministic"
    assert route.selected_provider == "deterministic"
