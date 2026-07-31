from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from aion_brain.contracts.model_gateway import (
    REFERENCE_JSON_MODEL_ID,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelStructuredOutputSchema,
    content_fingerprint,
    structured_schema_depth,
)
from aion_brain.contracts.secure_runtime import SecureRuntimeSessionState
from aion_brain.model_gateway.provider_adapter import (
    ControlledModelGatewayService,
    create_gateway_authorization_for_component,
)
from tests.secure_runtime_test_support import NOW, secure_runtime_fixture


@dataclass(frozen=True)
class GatewaySetup:
    service: ControlledModelGatewayService
    parent: object
    parent_session: object
    binding: object
    authorization: object
    plan: object
    session: object


@dataclass(frozen=True)
class GatewayFlow:
    setup: GatewaySetup
    messages: tuple[object, ...]
    context_items: tuple[object, ...]
    structured_schema: ModelStructuredOutputSchema | None
    context_decision: object
    token_decision: object
    request: object
    route: object
    fallback: object
    retry: object
    response: object
    validation: object
    classification: object
    provenance: object


def gateway_setup() -> GatewaySetup:
    parent = secure_runtime_fixture()
    parent_session = parent.session.model_copy(
        update={"current_state": SecureRuntimeSessionState.session_active}
    )
    service = ControlledModelGatewayService()
    binding = service.bind_secure_runtime_component(
        binding_id="binding-AION-233",
        secure_runtime_session=parent_session,
        parent_capability_plan=parent.capability_plan,
        parent_runtime_guard=parent.guard_decision,
        parent_simulated_dispatch=parent.dispatch,
        actor_context_binding_fingerprint=parent.actor_context.binding_fingerprint or "",
        invoked_at=NOW,
    )
    authorization = create_gateway_authorization_for_component(
        model_gateway_session_id="gateway-session-AION-233",
        component_binding=binding,
        operator_identity_fingerprint=parent.operator_identity.operator_identity_fingerprint,
        actor_context_binding_fingerprint=parent.actor_context.binding_fingerprint or "",
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=20),
    )
    plan = service.create_session_plan(
        session_plan_id="gateway-session-plan-AION-233",
        authorization_envelope=authorization,
        secure_runtime_session_fingerprint=parent_session.session_fingerprint or "",
        parent_capability_plan_fingerprint=parent.capability_plan.plan_fingerprint or "",
        parent_runtime_guard_fingerprint=parent.guard_decision.guard_decision_fingerprint or "",
        parent_simulated_dispatch_fingerprint=parent.dispatch.result_fingerprint or "",
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
    )
    session = service.start_session(plan)
    return GatewaySetup(
        service=service,
        parent=parent,
        parent_session=parent_session,
        binding=binding,
        authorization=authorization,
        plan=plan,
        session=session,
    )


def structured_schema() -> ModelStructuredOutputSchema:
    schema_definition = {
        "type": "object",
        "properties": {
            "summary": {"type": "string", "maxLength": 120},
            "synthetic": {"type": "boolean", "const": True},
            "trust": {"type": "string", "const": "untrusted"},
        },
        "required": ["summary", "synthetic", "trust"],
        "additionalProperties": False,
    }
    encoded = json.dumps(schema_definition, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return ModelStructuredOutputSchema(
        schema_id="schema-AION-233",
        schema_definition=schema_definition,
        schema_byte_count=len(encoded),
        schema_depth=structured_schema_depth(schema_definition),
    )


def gateway_flow(*, structured: bool = False) -> GatewayFlow:
    setup = gateway_setup()
    created_at = datetime(2026, 7, 31, 12, 1, tzinfo=UTC)
    messages = setup.service.normalize_messages(
        messages=(("message-AION-233", "user", "Summarize the redacted local test fixture."),),
        created_at=created_at,
    )
    context_items = setup.service.normalize_context(
        context_items=(
            ("context-AION-233", "fixture", "operator-local", "redacted fixture summary"),
        )
    )
    schema = structured_schema() if structured else None
    output_mode = (
        ModelGatewayOutputMode.structured_json if structured else ModelGatewayOutputMode.text
    )
    operation = (
        ModelGatewayOperation.structured_generate_simulate
        if structured
        else ModelGatewayOperation.text_generate_simulate
    )
    context_decision = setup.service.evaluate_context_budget(
        decision_id="context-budget-AION-233",
        budget=setup.authorization.context_budget,
        messages=messages,
        context_items=context_items,
        response_byte_limit=512,
        structured_schema=schema,
        created_at=created_at,
    )
    token_decision = setup.service.evaluate_token_budget(
        decision_id="token-budget-AION-233",
        budget=setup.authorization.token_budget,
        messages=messages,
        context_items=context_items,
        requested_output_tokens=512,
        current_session_tokens=0,
        created_at=created_at,
    )
    request = setup.service.build_request_envelope(
        request_envelope_id="request-AION-233",
        session=setup.session,
        secure_runtime_request_id=setup.parent.capability_plan.request_id,
        operation=operation,
        system_policy_code=(
            "aion-safe-structured-simulation-v1"
            if structured
            else "aion-safe-text-simulation-v1"
        ),
        messages=messages,
        context_items=context_items,
        context_budget_decision=context_decision,
        token_budget_decision=token_decision,
        output_mode=output_mode,
        requested_output_tokens=512,
        structured_schema=schema,
        safe_metadata={"purpose": "aion-233-test"},
        created_at=created_at,
        expires_at=created_at + timedelta(minutes=5),
    )
    route = setup.service.plan_route(
        routing_plan_id="route-AION-233",
        request=request,
        estimated_input_tokens=token_decision.usage.estimated_input_tokens,
        estimated_output_tokens=512,
        created_at=created_at,
    )
    fallback = setup.service.plan_fallback(
        fallback_plan_id="fallback-AION-233",
        request=request,
        routing_plan=route,
        created_at=created_at,
    )
    retry = setup.service.plan_retry(
        retry_plan_id="retry-AION-233",
        request=request,
        created_at=created_at,
    )
    model_id = route.selected_model_id or REFERENCE_JSON_MODEL_ID
    response = setup.service.simulate_reference_provider(
        reference_request_id="reference-AION-233",
        request=request,
        model_id=model_id,
        structured_schema=schema,
        created_at=created_at,
    )
    validation = setup.service.validate_response(
        validation_id="validation-AION-233",
        request=request,
        routing_plan=route,
        response=response,
        transient_output=response.transient_output,
        structured_schema=schema,
        created_at=created_at,
    )
    classification = setup.service.classify_untrusted_output(
        classification_id="classification-AION-233",
        response=response,
        validation=validation,
        created_at=created_at,
    )
    setup.service.record_audit(
        session_id=setup.session.session_id,
        request_id=request.request_envelope_id,
        event_type="response_validated",
        outcome=validation.status.value,
        payload={"validation": validation.validation_fingerprint},
        created_at=created_at,
    )
    provenance = setup.service.build_output_provenance(
        provenance_id="provenance-AION-233",
        request=request,
        routing_plan=route,
        response=response,
        validation=validation,
        classification=classification,
        audit_chain_head=setup.service.audit_ledger.chain_head(setup.session.session_id),
        created_at=created_at,
    )
    return GatewayFlow(
        setup=setup,
        messages=messages,
        context_items=context_items,
        structured_schema=schema,
        context_decision=context_decision,
        token_decision=token_decision,
        request=request,
        route=route,
        fallback=fallback,
        retry=retry,
        response=response,
        validation=validation,
        classification=classification,
        provenance=provenance,
    )


def safe_result_fingerprint(flow: GatewayFlow) -> str:
    return content_fingerprint("safe-result", flow.response.response_fingerprint or "")
