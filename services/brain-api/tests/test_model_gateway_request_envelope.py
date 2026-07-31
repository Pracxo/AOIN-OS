from __future__ import annotations

import pytest

from tests.model_gateway_aion233_test_support import gateway_flow


def test_request_envelope_has_no_prompt_endpoint_credential_tool_or_production_target() -> None:
    request = gateway_flow().request
    assert request.prompt_body_retained is False
    assert request.provider_credential_reference_present is False
    assert request.network_target_present is False
    assert request.connector_target_present is False
    assert request.tool_target_present is False
    assert request.executable_present is False
    assert request.production_target_present is False
    assert request.actual_provider_call is False
    assert request.request_fingerprint


def test_request_envelope_rejects_network_target() -> None:
    request = gateway_flow().request
    payload = request.model_dump(mode="python")
    payload["network_target_present"] = True
    payload.pop("request_fingerprint", None)
    with pytest.raises(ValueError):
        type(request).model_validate(payload)
