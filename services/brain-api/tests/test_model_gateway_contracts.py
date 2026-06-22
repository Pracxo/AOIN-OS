"""Model gateway contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.model_gateway import ModelGatewayRequest, ModelProfile, ModelProvider
from tests.model_gateway_fakes import gateway_request


def test_model_provider_validates_provider_type() -> None:
    with pytest.raises(ValidationError):
        ModelProvider(
            provider_id="provider-1",
            provider_type="unknown",
            display_name="Provider",
            status="active",
            endpoint_ref=None,
            config={},
            health_status="unknown",
        )


def test_model_provider_rejects_secret_like_config() -> None:
    with pytest.raises(ValidationError):
        ModelProvider(
            provider_id="provider-1",
            provider_type="local_http",
            display_name="Provider",
            status="active",
            endpoint_ref=None,
            config={"api_key": "secret"},
            health_status="unknown",
        )


def test_model_profile_validates_mode_privacy_and_token_limits() -> None:
    with pytest.raises(ValidationError):
        ModelProfile(
            model_profile_id="profile-1",
            provider_id="provider-1",
            model_name="model",
            mode="domain_specific",
            status="active",
            privacy_level="external",
            risk_level="low",
            max_input_tokens=0,
            max_output_tokens=100,
            latency_class="low",
            metadata={},
        )


def test_model_gateway_request_rejects_empty_scope() -> None:
    payload = gateway_request().model_dump(mode="python")
    payload["scope"] = []
    with pytest.raises(ValidationError):
        ModelGatewayRequest.model_validate(payload)
