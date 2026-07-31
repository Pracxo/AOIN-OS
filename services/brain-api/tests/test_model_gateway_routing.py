from __future__ import annotations

from tests.model_gateway_aion233_test_support import gateway_flow


def test_routing_is_deterministic_and_planning_only() -> None:
    flow = gateway_flow(structured=True)
    first = flow.route
    second = flow.setup.service.plan_route(
        routing_plan_id="route-AION-233",
        request=flow.request,
        estimated_input_tokens=flow.token_decision.usage.estimated_input_tokens,
        estimated_output_tokens=512,
        created_at=first.created_at,
    )
    assert first.selected_model_id == "reference-json-sim-v1"
    assert first.plan_fingerprint == second.plan_fingerprint
    assert first.planning_only is True
    assert first.automatic_execution is False
    assert first.provider_call_performed is False
    assert first.network_effect is False
