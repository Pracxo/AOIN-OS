"""Provider-adapter protocol and controlled model-gateway orchestration."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from typing import Any, Protocol

from aion_brain.contracts.model_gateway import (
    DETERMINISTIC_PROVIDER_ID,
    ModelFallbackPlan,
    ModelGatewayAuthorizationEnvelope,
    ModelGatewayComponentInvocationBinding,
    ModelGatewayContextBudget,
    ModelGatewayContextBudgetDecision,
    ModelGatewayContextItem,
    ModelGatewayContextUsage,
    ModelGatewayGuardDecision,
    ModelGatewayMessage,
    ModelGatewayMessageRole,
    ModelGatewayOperation,
    ModelGatewayOutputMode,
    ModelGatewayReferenceProviderRequest,
    ModelGatewayReferenceProviderResponse,
    ModelGatewayRequestEnvelope,
    ModelGatewayResponseClassification,
    ModelGatewaySession,
    ModelGatewaySessionPlan,
    ModelGatewaySystemInstructionPolicyBinding,
    ModelGatewayTokenBudget,
    ModelGatewayTokenBudgetDecision,
    ModelGatewayTokenUsage,
    ModelManifest,
    ModelOutputProvenance,
    ModelOutputValidationResult,
    ModelProviderManifest,
    ModelRetryPlan,
    ModelRoutingPlan,
    ModelStructuredOutputSchema,
    content_fingerprint,
    ensure_gateway_utc,
    estimate_tokens_from_bytes,
    model_gateway_fingerprint,
)
from aion_brain.contracts.secure_runtime import (
    SecureCapabilityInvocationPlan,
    SecureRuntimeGuardDecision,
    SecureRuntimeKillSwitchState,
    SecureRuntimeSession,
    SecureSimulatedDispatchResult,
)
from aion_brain.model_gateway.audit import InMemoryModelGatewayAuditLedger
from aion_brain.model_gateway.authorization import (
    InMemoryModelGatewaySessionRepository,
    bind_secure_runtime_component,
    create_authorization_envelope,
    create_session_plan,
    validate_authorization,
)
from aion_brain.model_gateway.circuit_breaker import (
    InMemoryModelCircuitBreakerRepository,
    closed_circuit_state,
)
from aion_brain.model_gateway.context_budget import (
    bind_system_instruction_policy,
    evaluate_context_budget,
    evaluate_token_budget,
    normalize_model_gateway_context_item,
    normalize_model_gateway_message,
)
from aion_brain.model_gateway.guard import ModelGatewayGuardEvaluator
from aion_brain.model_gateway.integrity import audit_integrity as build_integrity_report
from aion_brain.model_gateway.manifests import (
    InMemoryModelManifestRegistry,
    InMemoryModelProviderManifestRegistry,
)
from aion_brain.model_gateway.observability import (
    health_snapshot as build_health_snapshot,
)
from aion_brain.model_gateway.observability import (
    observability_snapshot as build_observability_snapshot,
)
from aion_brain.model_gateway.reference_provider import (
    DeterministicReferenceModelProvider,
    build_reference_provider_request,
)
from aion_brain.model_gateway.request_envelope import (
    InMemoryModelGatewayRequestRepository,
    build_request_envelope,
)
from aion_brain.model_gateway.response_validation import (
    build_output_provenance,
    classify_untrusted_output,
    validate_response,
)
from aion_brain.model_gateway.routing import (
    estimate_cost,
    estimate_latency,
    plan_fallback,
    plan_retry,
    plan_route,
)


class ModelProviderAdapter(Protocol):
    """Simulation-only provider adapter interface."""

    def simulate(
        self,
        *,
        reference_request: ModelGatewayReferenceProviderRequest,
        structured_schema: ModelStructuredOutputSchema | None,
        created_at: datetime,
    ) -> ModelGatewayReferenceProviderResponse:
        """Return deterministic simulated output."""

    def validate_adapter_state(self) -> bool:
        """Return true when the adapter remains simulation-only."""

    def adapter_manifest(self) -> Mapping[str, object]:
        """Return redacted no-endpoint adapter metadata."""


class ControlledModelGatewayService:
    """AION-233 controlled provider-neutral model gateway service."""

    def __init__(
        self,
        *,
        provider_registry: InMemoryModelProviderManifestRegistry | None = None,
        model_registry: InMemoryModelManifestRegistry | None = None,
        session_repository: InMemoryModelGatewaySessionRepository | None = None,
        request_repository: InMemoryModelGatewayRequestRepository | None = None,
        circuit_repository: InMemoryModelCircuitBreakerRepository | None = None,
        audit_ledger: InMemoryModelGatewayAuditLedger | None = None,
        reference_provider: ModelProviderAdapter | None = None,
    ) -> None:
        self.provider_registry = provider_registry or InMemoryModelProviderManifestRegistry()
        self.model_registry = model_registry or InMemoryModelManifestRegistry()
        self.session_repository = session_repository or InMemoryModelGatewaySessionRepository()
        self.request_repository = request_repository or InMemoryModelGatewayRequestRepository()
        self.circuit_repository = circuit_repository or InMemoryModelCircuitBreakerRepository()
        self.audit_ledger = audit_ledger or InMemoryModelGatewayAuditLedger()
        self.reference_provider = reference_provider or DeterministicReferenceModelProvider()
        self.guard_evaluator = ModelGatewayGuardEvaluator()

    def validate_authorization(self, envelope: ModelGatewayAuthorizationEnvelope) -> None:
        """Validate the exact AION-232 authorization envelope."""

        validate_authorization(envelope)

    def bind_secure_runtime_component(
        self,
        *,
        binding_id: str,
        secure_runtime_session: SecureRuntimeSession,
        parent_capability_plan: SecureCapabilityInvocationPlan,
        parent_runtime_guard: SecureRuntimeGuardDecision,
        parent_simulated_dispatch: SecureSimulatedDispatchResult,
        actor_context_binding_fingerprint: str,
        invoked_at: datetime,
    ) -> ModelGatewayComponentInvocationBinding:
        """Bind the AION-231 secure-runtime parent component."""

        return bind_secure_runtime_component(
            binding_id=binding_id,
            secure_runtime_session=secure_runtime_session,
            parent_capability_plan=parent_capability_plan,
            parent_runtime_guard=parent_runtime_guard,
            parent_simulated_dispatch=parent_simulated_dispatch,
            actor_context_binding_fingerprint=actor_context_binding_fingerprint,
            invoked_at=invoked_at,
        )

    def load_provider_manifests(self) -> tuple[ModelProviderManifest, ...]:
        """Load provider manifests from the closed immutable registry."""

        return self.provider_registry.list_manifests()

    def load_model_manifests(self) -> tuple[ModelManifest, ...]:
        """Load model manifests from the closed immutable registry."""

        return self.model_registry.list_manifests()

    def create_session_plan(
        self,
        *,
        session_plan_id: str,
        authorization_envelope: ModelGatewayAuthorizationEnvelope,
        secure_runtime_session_fingerprint: str,
        parent_capability_plan_fingerprint: str,
        parent_runtime_guard_fingerprint: str,
        parent_simulated_dispatch_fingerprint: str,
        created_at: datetime,
        expires_at: datetime,
    ) -> ModelGatewaySessionPlan:
        """Create the bounded model-gateway session plan."""

        providers = self.load_provider_manifests()
        models = self.load_model_manifests()
        return create_session_plan(
            session_plan_id=session_plan_id,
            authorization_envelope=authorization_envelope,
            secure_runtime_session_fingerprint=secure_runtime_session_fingerprint,
            parent_capability_plan_fingerprint=parent_capability_plan_fingerprint,
            parent_runtime_guard_fingerprint=parent_runtime_guard_fingerprint,
            parent_simulated_dispatch_fingerprint=parent_simulated_dispatch_fingerprint,
            provider_manifest_fingerprints=tuple(
                item.manifest_fingerprint or "" for item in providers
            ),
            model_manifest_fingerprints=tuple(item.manifest_fingerprint or "" for item in models),
            created_at=created_at,
            expires_at=expires_at,
        )

    def start_session(self, plan: ModelGatewaySessionPlan) -> ModelGatewaySession:
        """Start one model-gateway session."""

        session = self.session_repository.start_session(plan)
        self.record_audit(
            session_id=session.session_id,
            event_type="session_started",
            outcome="allowed",
            created_at=session.created_at,
        )
        return session

    def normalize_messages(
        self,
        *,
        messages: tuple[tuple[str, ModelGatewayMessageRole | str, str], ...],
        created_at: datetime,
    ) -> tuple[ModelGatewayMessage, ...]:
        """Normalize transient messages and drop raw content."""

        return tuple(
            normalize_model_gateway_message(
                message_id=message_id,
                role=role,
                content=content,
                created_at=created_at,
            )
            for message_id, role, content in messages
        )

    def normalize_context(
        self,
        *,
        context_items: tuple[tuple[str, str, str, str], ...],
    ) -> tuple[ModelGatewayContextItem, ...]:
        """Normalize transient context items and drop raw content."""

        return tuple(
            normalize_model_gateway_context_item(
                context_item_id=context_item_id,
                context_kind=context_kind,
                source=source,
                content=content,
            )
            for context_item_id, context_kind, source, content in context_items
        )

    def evaluate_context_budget(
        self,
        *,
        decision_id: str,
        budget: ModelGatewayContextBudget,
        messages: tuple[ModelGatewayMessage, ...],
        context_items: tuple[ModelGatewayContextItem, ...],
        response_byte_limit: int,
        structured_schema: ModelStructuredOutputSchema | None,
        created_at: datetime,
    ) -> ModelGatewayContextBudgetDecision:
        """Evaluate context budgets."""

        usage = ModelGatewayContextUsage(
            message_count=len(messages),
            context_item_count=len(context_items),
            prompt_utf8_bytes=sum(item.utf8_byte_count for item in messages),
            context_utf8_bytes=sum(item.utf8_byte_count for item in context_items),
            response_byte_limit=response_byte_limit,
            structured_schema_bytes=structured_schema.schema_byte_count if structured_schema else 0,
            structured_schema_depth=structured_schema.schema_depth if structured_schema else 0,
        )
        return evaluate_context_budget(
            decision_id=decision_id,
            budget=budget,
            usage=usage,
            created_at=created_at,
        )

    def evaluate_token_budget(
        self,
        *,
        decision_id: str,
        budget: ModelGatewayTokenBudget,
        messages: tuple[ModelGatewayMessage, ...],
        context_items: tuple[ModelGatewayContextItem, ...],
        requested_output_tokens: int,
        current_session_tokens: int,
        created_at: datetime,
    ) -> ModelGatewayTokenBudgetDecision:
        """Evaluate deterministic token-estimate budgets."""

        estimated_input_tokens = sum(item.deterministic_token_estimate for item in messages)
        estimated_input_tokens += sum(
            item.deterministic_token_estimate for item in context_items
        )
        usage = ModelGatewayTokenUsage(
            estimated_input_tokens=estimated_input_tokens,
            requested_output_tokens=requested_output_tokens,
            estimated_session_tokens_after_request=(
                current_session_tokens + estimated_input_tokens + requested_output_tokens
            ),
        )
        return evaluate_token_budget(
            decision_id=decision_id,
            budget=budget,
            usage=usage,
            created_at=created_at,
        )

    def build_request_envelope(
        self,
        *,
        request_envelope_id: str,
        session: ModelGatewaySession,
        secure_runtime_request_id: str,
        operation: ModelGatewayOperation,
        system_policy_code: str,
        messages: tuple[ModelGatewayMessage, ...],
        context_items: tuple[ModelGatewayContextItem, ...],
        context_budget_decision: ModelGatewayContextBudgetDecision,
        token_budget_decision: ModelGatewayTokenBudgetDecision,
        output_mode: ModelGatewayOutputMode,
        requested_output_tokens: int,
        structured_schema: ModelStructuredOutputSchema | None,
        safe_metadata: Mapping[str, object] | None,
        created_at: datetime,
        expires_at: datetime,
    ) -> ModelGatewayRequestEnvelope:
        """Build a request envelope without raw prompt retention."""

        policy = self.bind_system_instruction_policy(
            policy_code=system_policy_code, created_at=created_at
        )
        return build_request_envelope(
            request_envelope_id=request_envelope_id,
            session=session,
            secure_runtime_request_id=secure_runtime_request_id,
            operation=operation,
            system_policy=policy,
            messages=messages,
            context_items=context_items,
            context_budget_decision=context_budget_decision,
            token_budget_decision=token_budget_decision,
            output_mode=output_mode,
            requested_output_tokens=requested_output_tokens,
            structured_schema=structured_schema,
            safe_metadata=safe_metadata,
            created_at=created_at,
            expires_at=expires_at,
        )

    def bind_system_instruction_policy(
        self, *, policy_code: str, created_at: datetime
    ) -> ModelGatewaySystemInstructionPolicyBinding:
        """Bind a closed system-instruction policy."""

        return bind_system_instruction_policy(policy_code=policy_code, created_at=created_at)

    def check_request_idempotency(
        self, request: ModelGatewayRequestEnvelope
    ) -> tuple[str, object | None]:
        """Check exact replay and reject changed replay."""

        return self.request_repository.check_request_idempotency(request)

    def plan_route(
        self,
        *,
        routing_plan_id: str,
        request: ModelGatewayRequestEnvelope,
        estimated_input_tokens: int,
        estimated_output_tokens: int,
        created_at: datetime,
    ) -> ModelRoutingPlan:
        """Create a deterministic route plan."""

        provider = self.provider_registry.get(DETERMINISTIC_PROVIDER_ID)
        models = self.model_registry.list_manifests()
        profiles = self.model_registry.list_profiles()
        circuit_states = tuple(
            self.circuit_repository.state_for_model(model.model_id) for model in models
        )
        return plan_route(
            routing_plan_id=routing_plan_id,
            request=request,
            provider_manifest=provider,
            model_manifests=models,
            capability_profiles=profiles,
            circuit_states=circuit_states,
            estimated_input_tokens=estimated_input_tokens,
            estimated_output_tokens=estimated_output_tokens,
            created_at=created_at,
        )

    def plan_fallback(
        self,
        *,
        fallback_plan_id: str,
        request: ModelGatewayRequestEnvelope,
        routing_plan: ModelRoutingPlan,
        created_at: datetime,
    ) -> ModelFallbackPlan:
        """Create a deterministic fallback plan."""

        return plan_fallback(
            fallback_plan_id=fallback_plan_id,
            request=request,
            routing_plan=routing_plan,
            created_at=created_at,
        )

    def plan_retry(
        self,
        *,
        retry_plan_id: str,
        request: ModelGatewayRequestEnvelope,
        created_at: datetime,
    ) -> ModelRetryPlan:
        """Create a deterministic retry plan with execution disabled."""

        return plan_retry(
            retry_plan_id=retry_plan_id,
            request=request,
            created_at=created_at,
        )

    def evaluate_circuit_breaker(self, model_id: str) -> object:
        """Return the current circuit-breaker state."""

        return self.circuit_repository.state_for_model(model_id) or closed_circuit_state(model_id)

    def evaluate_guard(
        self,
        *,
        decision_id: str,
        authorization: ModelGatewayAuthorizationEnvelope,
        component_binding: ModelGatewayComponentInvocationBinding,
        secure_runtime_session: SecureRuntimeSession,
        parent_capability_plan: SecureCapabilityInvocationPlan,
        parent_runtime_guard: SecureRuntimeGuardDecision,
        parent_kill_switch: SecureRuntimeKillSwitchState,
        gateway_session: ModelGatewaySession,
        request: ModelGatewayRequestEnvelope,
        routing_plan: ModelRoutingPlan,
        fallback_plan: ModelFallbackPlan,
        retry_plan: ModelRetryPlan,
        context_budget_decision: ModelGatewayContextBudgetDecision,
        token_budget_decision: ModelGatewayTokenBudgetDecision,
        model_manifest: ModelManifest,
        created_at: datetime,
    ) -> ModelGatewayGuardDecision:
        """Evaluate the no-effect model gateway guard."""

        provider = self.provider_registry.get(DETERMINISTIC_PROVIDER_ID)
        profile = next(
            item
            for item in self.model_registry.list_profiles()
            if item.model_id == model_manifest.model_id
        )
        circuit = self.circuit_repository.state_for_model(model_manifest.model_id)
        cost = estimate_cost(
            estimated_input_tokens=routing_plan.candidates[0].estimated_input_tokens,
            estimated_output_tokens=routing_plan.candidates[0].estimated_output_tokens,
        )
        latency = estimate_latency(
            estimated_input_tokens=routing_plan.candidates[0].estimated_input_tokens,
            estimated_output_tokens=routing_plan.candidates[0].estimated_output_tokens,
        )
        return self.guard_evaluator.evaluate(
            decision_id=decision_id,
            authorization=authorization,
            component_binding=component_binding,
            secure_runtime_session=secure_runtime_session,
            parent_capability_plan=parent_capability_plan,
            parent_runtime_guard=parent_runtime_guard,
            parent_kill_switch=parent_kill_switch,
            gateway_session=gateway_session,
            request=request,
            provider_manifest=provider,
            model_manifest=model_manifest,
            capability_profile_fingerprint=profile.profile_fingerprint or "",
            context_budget_decision=context_budget_decision,
            token_budget_decision=token_budget_decision,
            routing_plan=routing_plan,
            fallback_plan=fallback_plan,
            retry_plan=retry_plan,
            circuit_breaker_state=circuit,
            cost_estimate=cost,
            latency_estimate=latency,
            created_at=created_at,
        )

    def simulate_reference_provider(
        self,
        *,
        reference_request_id: str,
        request: ModelGatewayRequestEnvelope,
        model_id: str,
        structured_schema: ModelStructuredOutputSchema | None,
        created_at: datetime,
    ) -> ModelGatewayReferenceProviderResponse:
        """Run deterministic local reference-provider simulation."""

        reference_request = build_reference_provider_request(
            reference_request_id=reference_request_id,
            model_id=model_id,
            request_fingerprint=request.request_fingerprint or "",
            operation=request.operation,
            output_mode=request.requested_output_mode,
            requested_output_tokens=request.requested_output_tokens,
            structured_schema=structured_schema,
            created_at=created_at,
        )
        return self.reference_provider.simulate(
            reference_request=reference_request,
            structured_schema=structured_schema,
            created_at=created_at,
        )

    def validate_response(
        self,
        *,
        validation_id: str,
        request: ModelGatewayRequestEnvelope,
        routing_plan: ModelRoutingPlan,
        response: ModelGatewayReferenceProviderResponse,
        transient_output: Any,
        structured_schema: ModelStructuredOutputSchema | None,
        created_at: datetime,
    ) -> ModelOutputValidationResult:
        """Validate a simulated response as untrusted output."""

        provider = self.provider_registry.get(DETERMINISTIC_PROVIDER_ID)
        model = self.model_registry.get(response.model_id)
        return validate_response(
            validation_id=validation_id,
            request=request,
            provider_manifest=provider,
            model_manifest=model,
            route_plan=routing_plan,
            response=response,
            transient_output=transient_output,
            structured_schema=structured_schema,
            created_at=created_at,
        )

    def classify_untrusted_output(
        self,
        *,
        classification_id: str,
        response: ModelGatewayReferenceProviderResponse,
        validation: ModelOutputValidationResult,
        created_at: datetime,
    ) -> ModelGatewayResponseClassification:
        """Classify output as untrusted."""

        return classify_untrusted_output(
            classification_id=classification_id,
            response=response,
            validation=validation,
            created_at=created_at,
        )

    def build_output_provenance(
        self,
        *,
        provenance_id: str,
        request: ModelGatewayRequestEnvelope,
        routing_plan: ModelRoutingPlan,
        response: ModelGatewayReferenceProviderResponse,
        validation: ModelOutputValidationResult,
        classification: ModelGatewayResponseClassification,
        audit_chain_head: str,
        created_at: datetime,
    ) -> ModelOutputProvenance:
        """Build redacted output provenance."""

        return build_output_provenance(
            provenance_id=provenance_id,
            provider_manifest=self.provider_registry.get(DETERMINISTIC_PROVIDER_ID),
            model_manifest=self.model_registry.get(response.model_id),
            request=request,
            route_plan=routing_plan,
            response=response,
            validation=validation,
            classification=classification,
            audit_chain_head=audit_chain_head,
            created_at=created_at,
        )

    def record_audit(
        self,
        *,
        session_id: str,
        event_type: str,
        outcome: str,
        created_at: datetime,
        request_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> object:
        """Record a redacted audit event."""

        return self.audit_ledger.append(
            session_id=session_id,
            request_id=request_id,
            event_type=event_type,
            outcome=outcome,
            payload=payload,
            created_at=ensure_gateway_utc(created_at),
        )

    def observability_snapshot(
        self,
        *,
        snapshot_id: str,
        session_id: str,
        event_counters: dict[str, int],
        health_state: str,
        created_at: datetime,
    ) -> object:
        """Return a redacted observability snapshot."""

        return build_observability_snapshot(
            snapshot_id=snapshot_id,
            session_id=session_id,
            event_counters=event_counters,
            health_state=health_state,
            audit_chain_head=self.audit_ledger.chain_head(session_id),
            created_at=created_at,
        )

    def health_snapshot(self, *, health_id: str, health_state: str, created_at: datetime) -> object:
        """Return a gateway readiness health snapshot."""

        return build_health_snapshot(
            health_id=health_id,
            health_state=health_state,
            created_at=created_at,
            reference_provider_available=self.reference_provider.validate_adapter_state(),
        )

    def audit_integrity(
        self,
        *,
        report_id: str,
        session_id: str,
        checked_categories: tuple[str, ...],
        created_at: datetime,
    ) -> object:
        """Audit the gateway no-effect evidence chain."""

        return build_integrity_report(
            report_id=report_id,
            session_id=session_id,
            audit_chain_head=self.audit_ledger.chain_head(session_id),
            checked_categories=checked_categories,
            created_at=created_at,
        )

    def replay_fixture(self, request: ModelGatewayRequestEnvelope) -> tuple[str, object | None]:
        """Replay an exact fixture or reject changed replay."""

        return self.check_request_idempotency(request)

    def close_request(
        self, *, session_id: str, request_id: str, created_at: datetime
    ) -> ModelGatewaySession:
        """Close one request and release active references."""

        session = self.session_repository.close_request(session_id, request_id)
        self.record_audit(
            session_id=session_id,
            request_id=request_id,
            event_type="request_closed",
            outcome="closed",
            created_at=created_at,
        )
        return session

    def close_session(self, *, session_id: str, closed_at: datetime) -> ModelGatewaySession:
        """Close a gateway session."""

        session = self.session_repository.close_session(session_id, closed_at)
        self.record_audit(
            session_id=session_id,
            event_type="session_closed",
            outcome="closed",
            created_at=closed_at,
        )
        return session

    def reject_live_provider_call(self) -> None:
        """Fail closed for any attempted live provider path."""

        raise PermissionError("live model provider calls are not authorized")

    def reject_external_effect(self) -> None:
        """Fail closed for any attempted external effect."""

        raise PermissionError("external effects are not authorized")


def create_gateway_authorization_for_component(
    *,
    model_gateway_session_id: str,
    component_binding: ModelGatewayComponentInvocationBinding,
    operator_identity_fingerprint: str,
    actor_context_binding_fingerprint: str,
    created_at: datetime,
    expires_at: datetime,
) -> ModelGatewayAuthorizationEnvelope:
    """Convenience builder for exact AION-232 authorization envelopes."""

    return create_authorization_envelope(
        model_gateway_session_id=model_gateway_session_id,
        secure_runtime_component_binding=component_binding,
        operator_identity_fingerprint=operator_identity_fingerprint,
        actor_context_binding_fingerprint=actor_context_binding_fingerprint,
        created_at=created_at,
        expires_at=expires_at,
    )


def retained_output_fingerprint(output: object) -> str:
    """Return a fingerprint for output without retaining the output."""

    encoded = str(output).encode("utf-8")
    return model_gateway_fingerprint(
        {
            "output_fingerprint": content_fingerprint("controlled_gateway_output", encoded),
            "estimated_tokens": estimate_tokens_from_bytes(len(encoded)),
        }
    )
