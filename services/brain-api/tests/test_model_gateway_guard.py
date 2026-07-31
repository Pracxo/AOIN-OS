from __future__ import annotations

from tests.model_gateway_aion233_test_support import gateway_flow


def test_guard_allows_reference_simulation_and_no_live_effect() -> None:
    flow = gateway_flow(structured=True)
    model = flow.setup.service.model_registry.get(flow.route.selected_model_id or "")
    decision = flow.setup.service.evaluate_guard(
        decision_id="guard-AION-233",
        authorization=flow.setup.authorization,
        component_binding=flow.setup.binding,
        secure_runtime_session=flow.setup.parent_session,
        parent_capability_plan=flow.setup.parent.capability_plan,
        parent_runtime_guard=flow.setup.parent.guard_decision,
        parent_kill_switch=flow.setup.parent.kill_switch_state,
        gateway_session=flow.setup.session,
        request=flow.request,
        routing_plan=flow.route,
        fallback_plan=flow.fallback,
        retry_plan=flow.retry,
        context_budget_decision=flow.context_decision,
        token_budget_decision=flow.token_decision,
        model_manifest=model,
        created_at=flow.setup.plan.created_at,
    )
    assert decision.outcome.value == "allow_reference_simulation"
    assert decision.allow_provider_call is False
    assert decision.allow_network_egress is False
    assert decision.allow_tool_call is False
    assert decision.allow_function_call is False
    assert decision.allow_production_execution is False
