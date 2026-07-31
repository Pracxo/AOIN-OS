from __future__ import annotations

from aion_brain.model_gateway.response_validation import validate_response
from tests.model_gateway_aion233_test_support import gateway_flow


def test_response_validation_passes_safe_output_and_blocks_smuggled_actions() -> None:
    flow = gateway_flow()
    assert flow.validation.status.value == "passed"
    blocked = validate_response(
        validation_id="validation-smuggled",
        request=flow.request,
        provider_manifest=flow.setup.service.provider_registry.get("deterministic-reference-provider"),
        model_manifest=flow.setup.service.model_registry.get(flow.response.model_id),
        route_plan=flow.route,
        response=flow.response,
        transient_output={"tool_calls": [{"name": "run"}]},
        structured_schema=None,
        created_at=flow.setup.plan.created_at,
    )
    assert blocked.status.value == "blocked"
    assert "smuggled_tool_or_function_call" in blocked.reason_codes
    assert blocked.trusted is False
    assert blocked.tool_effect is False
