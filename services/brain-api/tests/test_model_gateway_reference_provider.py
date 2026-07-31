from __future__ import annotations

from tests.model_gateway_aion233_test_support import gateway_flow


def test_reference_provider_simulates_text_and_structured_without_live_effects() -> None:
    text = gateway_flow()
    structured = gateway_flow(structured=True)
    for response in (text.response, structured.response):
        assert response.synthetic is True
        assert response.simulation_only is True
        assert response.actual_provider_call is False
        assert response.network_effect is False
        assert response.credential_effect is False
        assert response.tool_effect is False
        assert response.production_effect is False
    assert text.response.output_mode.value == "text"
    assert structured.response.output_mode.value == "structured_json"
