from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.external_cognition import (
    AUTHORIZATION_TRANSACTION_ID,
    EXTERNAL_COGNITION_AUTHORIZATION_SCHEMA_VERSION,
    EXTERNAL_COGNITION_CONTRACT_SCHEMA_VERSION,
    FINAL_PLANNED_TASK,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    PROHIBITED_EFFECT_COUNTERS,
    ZERO_FINGERPRINT,
    ExternalCognitionBudgetOutcome,
    ExternalCognitionCapabilityKind,
    ExternalCognitionCircuitState,
    ExternalCognitionContextBudget,
    ExternalCognitionCostBudget,
    ExternalCognitionOutputBudget,
    ExternalCognitionProviderErrorClass,
    ExternalCognitionProviderKind,
    ExternalCognitionReplayOutcome,
    ExternalCognitionRequestEnvelope,
    ExternalCognitionRequestIntent,
    ExternalCognitionStructuredOutputSchema,
    ExternalCognitionTrustClass,
    InMemoryExternalCognitionProviderRegistry,
    external_cognition_fingerprint,
)
from aion_brain.external_cognition import ControlledExternalCognitionService
from aion_brain.external_cognition.integrity import (
    create_default_authorization,
    create_default_component_binding,
    default_budgets,
    default_route_policies,
    default_structured_output_schemas,
)

ROOT = Path(__file__).resolve().parents[3]
NOW = datetime(2026, 8, 3, 20, 45, tzinfo=UTC)
MAIN_COMMIT = "d7fe689bfe39a98688784758ceb2b7130ca949bd"


def _setup() -> tuple[ControlledExternalCognitionService, object, object, object]:
    service = ControlledExternalCognitionService()
    authorization = create_default_authorization(created_at=NOW)
    binding = create_default_component_binding(
        current_main_commit=MAIN_COMMIT,
        created_at=NOW,
    )
    plan = service.create_session_plan(
        session_plan_id="external-cognition-plan-aion-246",
        authorization_envelope=authorization,
        component_binding=binding,
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=15),
    )
    session = service.start_session(plan)
    return service, authorization, binding, session


def _request(
    service: ControlledExternalCognitionService,
    authorization: object,
    binding: object,
    session: object,
    *,
    request_id: str = "external-cognition-request-aion-246",
    content: str = "deterministic fixture request",
    intent: ExternalCognitionRequestIntent = ExternalCognitionRequestIntent.reasoning,
    capability: ExternalCognitionCapabilityKind = (
        ExternalCognitionCapabilityKind.general_reasoning
    ),
    policy_index: int = 0,
    schema: ExternalCognitionStructuredOutputSchema | None = None,
) -> ExternalCognitionRequestEnvelope:
    context, output, cost, latency, *_ = default_budgets()
    messages = service.normalize_messages(
        messages=(("message-aion-246", "user", content),),
        normalized_at=NOW,
    )
    return service.create_request_envelope(
        request_id=request_id,
        session=session,
        authorization=authorization,  # type: ignore[arg-type]
        component_binding=binding,  # type: ignore[arg-type]
        request_intent=intent,
        requested_capability_codes=(capability,),
        messages=messages,
        context_budget=context,
        output_budget=output,
        cost_budget=cost,
        latency_budget=latency,
        route_policy=default_route_policies()[policy_index],
        structured_output_schema=schema,
        safe_metadata={"purpose": "aion-246-test"},
        created_at=NOW,
        expires_at=NOW + timedelta(minutes=5),
    )


def test_contract_constants_and_zero_effect_counter_set() -> None:
    assert EXTERNAL_COGNITION_CONTRACT_SCHEMA_VERSION == "aion-external-cognition/v1"
    assert EXTERNAL_COGNITION_AUTHORIZATION_SCHEMA_VERSION.endswith("/v1")
    assert PROGRAM_ID == "AION-ADAPTIVE-INTELLIGENCE-001"
    assert AUTHORIZATION_TRANSACTION_ID == "AION-245-AI-0001"
    assert IMPLEMENTATION_TASK == "AION-246"
    assert FORMAL_CLOSEOUT_TASK == "AION-247"
    assert FINAL_PLANNED_TASK == "AION-260"
    assert all(value == 0 for value in PROHIBITED_EFFECT_COUNTERS.values())


def test_authorization_and_component_binding_are_no_effect() -> None:
    service, authorization, binding, session = _setup()
    assert service.validate_authorization(authorization).authorization_transaction_id
    assert authorization.network_enabled is False
    assert authorization.credential_input_enabled is False
    assert authorization.memory_write is False
    assert authorization.tool_execution is False
    assert binding.current_main_commit == MAIN_COMMIT
    assert binding.network_effect is False
    assert binding.provider_effect is False
    assert binding.memory_effect is False
    assert binding.tool_effect is False
    assert session.session_plan.maximum_concurrent_requests == 4


def test_provider_model_and_capability_manifests_are_immutable_and_referential() -> None:
    service = ControlledExternalCognitionService()
    providers = service.load_provider_manifests()
    models = service.load_model_manifests()
    capabilities = service.load_capability_records()
    assert len(providers) == 3
    assert len(models) == 6
    assert len(capabilities) == 18
    assert {provider.provider_kind for provider in providers} == {
        ExternalCognitionProviderKind.deterministic_fixture,
    }
    with pytest.raises(ValidationError):
        providers[0].provider_id = "mutated"  # type: ignore[misc]
    with pytest.raises(ValueError):
        InMemoryExternalCognitionProviderRegistry((providers[0], providers[0]))
    with pytest.raises((KeyError, ValueError)):
        ControlledExternalCognitionService().load_model_manifests(
            models=(
                models[0].model_copy(
                    update={
                        "provider_id": "missing-provider",
                        "manifest_fingerprint": None,
                    }
                ),
            ),
            capabilities=capabilities,
        )


def test_message_projection_redacts_without_retaining_body() -> None:
    service = ControlledExternalCognitionService()
    projections = service.normalize_messages(
        messages=(("message-protected", "user", "password value is present"),),
        normalized_at=NOW,
    )
    projection = projections[0]
    dumped = projection.model_dump(mode="json")
    assert projection.protected_material_present is True
    assert projection.redaction_finding_count == 1
    assert "password value" not in json.dumps(dumped)
    assert "content_fingerprint" in dumped


def test_request_envelope_rejects_execution_and_provider_material() -> None:
    service, authorization, binding, session = _setup()
    request = _request(service, authorization, binding, session)
    data = request.model_dump(mode="python")
    data["request_fingerprint"] = None
    data["tool_execution_requested"] = True
    with pytest.raises(ValidationError):
        ExternalCognitionRequestEnvelope(**data)
    data = request.model_dump(mode="python")
    data["request_fingerprint"] = None
    data["provider_headers_present"] = True
    with pytest.raises(ValidationError):
        ExternalCognitionRequestEnvelope(**data)


def test_restricted_structured_schema_and_validation_remain_untrusted() -> None:
    service = ControlledExternalCognitionService()
    schema = default_structured_output_schemas()[0]
    accepted = service.validate_structured_response(
        validation_id="structured-validation-accepted",
        schema=schema,
        transient_output={"label": "fixture", "score": 0.5},
        created_at=NOW,
    )
    rejected = service.validate_structured_response(
        validation_id="structured-validation-rejected",
        schema=schema,
        transient_output={"label": "", "score": 2},
        created_at=NOW,
    )
    assert accepted.accepted is True
    assert accepted.trust_class == ExternalCognitionTrustClass.schema_validated_untrusted
    assert accepted.factual_truth_confirmed is False
    assert rejected.accepted is False
    assert rejected.trust_class == ExternalCognitionTrustClass.rejected
    with pytest.raises(ValidationError):
        ExternalCognitionStructuredOutputSchema(
            schema_id="bad-ref-schema",
            schema_definition={"$ref": "#/defs/value"},
            schema_depth=1,
            property_count=0,
        )
    with pytest.raises(ValidationError):
        ExternalCognitionStructuredOutputSchema(
            schema_id="bad-additional-schema",
            schema_definition={"type": "object", "additionalProperties": True},
            schema_depth=1,
            property_count=0,
        )


def test_budget_decisions_fail_closed() -> None:
    service = ControlledExternalCognitionService()
    messages = service.normalize_messages(
        messages=(("message-budget", "user", "over limit payload"),),
        normalized_at=NOW,
    )
    context = service.evaluate_context_budget(
        decision_id="context-budget-reject",
        budget=ExternalCognitionContextBudget(
            maximum_payload_bytes=1,
            maximum_declared_context_tokens=1,
        ),
        messages=messages,
        created_at=NOW,
    )
    output = service.evaluate_output_budget(
        decision_id="output-budget-reject",
        budget=ExternalCognitionOutputBudget(
            maximum_output_tokens=1,
            maximum_response_payload_bytes=1,
        ),
        requested_output_tokens=2,
        response_payload_bytes=2,
        created_at=NOW,
    )
    cost = service.evaluate_cost_budget(
        decision_id="cost-budget-reject",
        budget=ExternalCognitionCostBudget(maximum_declared_cost_units=1),
        declared_cost_units=2,
        created_at=NOW,
    )
    assert context.outcome == ExternalCognitionBudgetOutcome.rejected
    assert output.outcome == ExternalCognitionBudgetOutcome.rejected
    assert cost.outcome == ExternalCognitionBudgetOutcome.rejected
    assert context.override_allowed is False
    assert output.override_allowed is False
    assert cost.override_allowed is False


def test_policy_routing_retry_fallback_and_circuit_breaker_are_deterministic() -> None:
    service, authorization, binding, session = _setup()
    request = _request(service, authorization, binding, session)
    route = service.plan_route(
        route_plan_id="route-aion-246",
        request=request,
        policy=default_route_policies()[0],
        created_at=NOW,
    )
    assert route.selected_model_id == "fixture-reasoner-large-v1"
    assert route.existing_model_gateway_compatible is True
    fallback = service.plan_fallback(
        fallback_plan_id="fallback-aion-246",
        route_plan=route,
    )
    assert fallback.fallback_eligible is True
    assert fallback.fallback_model_id == "fixture-reasoner-small-v1"
    error = service.normalize_provider_error(
        normalization_id="provider-error-timeout",
        error_id="provider-timeout",
        error_class=ExternalCognitionProviderErrorClass.timeout,
    )
    retry = service.plan_retry(
        retry_plan_id="retry-aion-246",
        request=request,
        policy=default_budgets()[4],
        error=error.normalized_error,
    )
    assert retry.planned_attempts == 3
    first = service.evaluate_circuit_breaker(
        decision_id="circuit-first",
        model_id=route.selected_model_id or "",
        record_failure=True,
    )
    second = service.evaluate_circuit_breaker(
        decision_id="circuit-second",
        model_id=route.selected_model_id or "",
        record_failure=True,
    )
    assert first.next_state.state == ExternalCognitionCircuitState.closed
    assert second.next_state.state == ExternalCognitionCircuitState.open
    assert second.allowed is False


def test_fixture_response_replay_trust_uncertainty_and_audit_are_redacted() -> None:
    service, authorization, binding, session = _setup()
    request = _request(service, authorization, binding, session)
    route = service.plan_route(
        route_plan_id="route-response-aion-246",
        request=request,
        policy=default_route_policies()[0],
        created_at=NOW,
    )
    fixture = service.invoke_deterministic_fixture(fixture_id="fixture-general")
    trust = service.assess_trust(
        trust_assessment_id="trust-response-aion-246",
        validation=None,
        created_at=NOW,
    )
    response = service.project_response(
        response_id="response-aion-246",
        request=request,
        route_plan=route,
        fixture_response=fixture,
        trust_assessment=trust,
        validation=None,
        fallback_plan=None,
        retry_plan=None,
        created_at=NOW,
    )
    service.record_audit(
        session_id=session.session_id,  # type: ignore[attr-defined]
        event_type="response_projected",
        outcome="accepted",
        subject_fingerprint=response.response_fingerprint or ZERO_FINGERPRINT,
        created_at=NOW,
    )
    replay = service.replay_exact_request(
        request=request,
        safe_response_fingerprint=response.response_fingerprint or ZERO_FINGERPRINT,
        created_at=NOW,
    )
    exact = service.replay_exact_request(
        request=request,
        safe_response_fingerprint=response.response_fingerprint or ZERO_FINGERPRINT,
        created_at=NOW,
    )
    changed_request = _request(
        service,
        authorization,
        binding,
        session,
        request_id=request.request_id,
        content="changed deterministic fixture request",
    )
    changed = service.reject_changed_replay(
        request=changed_request,
        safe_response_fingerprint=response.response_fingerprint or ZERO_FINGERPRINT,
        created_at=NOW,
    )
    assert replay.outcome == ExternalCognitionReplayOutcome.new
    assert exact.outcome == ExternalCognitionReplayOutcome.exact_replay
    assert exact.fixture_invoked is False
    assert changed.outcome == ExternalCognitionReplayOutcome.changed_replay_rejected
    assert response.raw_response_absent is True
    assert response.production_effect is False
    serialized = json.dumps(response.model_dump(mode="json"))
    assert "fixture-general-result" not in serialized
    assert trust.factual_truth_confirmed is False
    assert response.uncertainty_projection.operator_review_required is True


def test_observability_integrity_and_evidence_require_zero_effects() -> None:
    service, _, _, session = _setup()
    evidence_chain_head = external_cognition_fingerprint({"evidence": "aion-246"})
    counters = {
        "provider_manifests_loaded": 3,
        "model_manifests_loaded": 6,
        "model_capability_records_loaded": 18,
    }
    observability = service.create_observability_snapshot(
        snapshot_id="observability-aion-246",
        session_id=session.session_id,  # type: ignore[attr-defined]
        counters=counters,
        trust_class_counts={"untrusted_fixture_output": 1},
        uncertainty_counts={"operator_review_required": 1},
        circuit_states={"fixture-reasoner-large-v1": "closed"},
        evidence_chain_head=evidence_chain_head,
        created_at=NOW,
    )
    integrity = service.audit_integrity(
        report_id="integrity-aion-246",
        session_id=session.session_id,  # type: ignore[attr-defined]
        evidence_chain_head=evidence_chain_head,
        prohibited_effect_counters=PROHIBITED_EFFECT_COUNTERS,
        created_at=NOW,
    )
    evidence = service.create_evidence_bundle(
        evidence_id="evidence-aion-246",
        session_id=session.session_id,  # type: ignore[attr-defined]
        observability=observability,
        integrity=integrity,
        counters=counters,
        prohibited_effect_counters=PROHIBITED_EFFECT_COUNTERS,
        evidence_chain_head=evidence_chain_head,
        created_at=NOW,
    )
    assert integrity.status.value == "passed"
    assert evidence.redacted is True
    assert evidence.provider_effect is False
    assert evidence.network_effect is False
    assert evidence.memory_effect is False
    assert evidence.tool_effect is False
    assert all(value == 0 for value in evidence.prohibited_effect_counters.values())


def test_committed_fixture_pilot_evidence_is_redacted_and_machine_verifiable() -> None:
    path = ROOT / "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json"
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected = external_cognition_fingerprint(
        {key: value for key, value in payload.items() if key != "report_fingerprint"}
    )
    assert payload["report_fingerprint"] == expected
    assert payload["pilot_id"] == "AION-246-deterministic-external-cognition-fixture-pilot"
    assert payload["program_id"] == PROGRAM_ID
    assert payload["authorization_id"] == AUTHORIZATION_TRANSACTION_ID
    assert payload["implementation_commit"]
    assert payload["integrity_passed"] is True
    assert payload["redacted"] is True
    assert payload["provider_effect"] is False
    assert payload["network_effect"] is False
    assert payload["memory_effect"] is False
    assert payload["tool_effect"] is False
    assert payload["production_effect"] is False
    assert all(value == 0 for value in payload["prohibited_effect_counters"].values())
    assert payload["counters"]["provider_manifests_loaded"] == 3
    assert payload["counters"]["model_manifests_loaded"] == 6
    assert payload["counters"]["model_capability_records_loaded"] == 18
    assert payload["counters"]["fixture_requests_submitted"] == 16
    assert payload["counters"]["temporary_files_retained"] == 0
    serialized = json.dumps(payload, sort_keys=True).lower()
    for marker in ("chain-of-thought", "bearer ", "sk-", "temporary-root"):
        assert marker not in serialized
    assert "fixture-general-result" not in serialized
