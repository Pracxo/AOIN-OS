from __future__ import annotations

from tests.model_gateway_aion233_test_support import gateway_flow


def test_reference_simulation_is_deterministic_and_bounded() -> None:
    flow = gateway_flow(structured=True)
    second = flow.setup.service.simulate_reference_provider(
        reference_request_id="reference-AION-233",
        request=flow.request,
        model_id=flow.route.selected_model_id or "reference-json-sim-v1",
        structured_schema=flow.structured_schema,
        created_at=flow.setup.plan.created_at,
    )
    assert flow.response.output_fingerprint == second.output_fingerprint
    assert flow.response.output_byte_count <= 1_048_576
    assert flow.response.estimated_output_tokens <= 512
