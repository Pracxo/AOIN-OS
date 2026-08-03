"""Controlled external-cognition service and integrity helpers."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta

from aion_brain.contracts.external_cognition import (
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    MAXIMUM_RETRY_ATTEMPTS,
    PROGRAM_ID,
    PROHIBITED_EFFECT_COUNTERS,
    ZERO_FINGERPRINT,
    DeterministicExternalCognitionFixtureProvider,
    ExternalCognitionAuthorizationEnvelope,
    ExternalCognitionBudgetDecision,
    ExternalCognitionBudgetOutcome,
    ExternalCognitionCapabilityKind,
    ExternalCognitionCircuitBreakerDecision,
    ExternalCognitionCircuitBreakerPolicy,
    ExternalCognitionCircuitState,
    ExternalCognitionComponentBinding,
    ExternalCognitionContextBudget,
    ExternalCognitionCostBudget,
    ExternalCognitionEvidenceBundle,
    ExternalCognitionFallbackPlan,
    ExternalCognitionFixtureRecord,
    ExternalCognitionIntegrityReport,
    ExternalCognitionIntegrityStatus,
    ExternalCognitionLatencyBudget,
    ExternalCognitionMessageProjection,
    ExternalCognitionMessageRole,
    ExternalCognitionModelCapabilityRecord,
    ExternalCognitionModelManifest,
    ExternalCognitionObservabilitySnapshot,
    ExternalCognitionOperatorReviewRecord,
    ExternalCognitionOutputBudget,
    ExternalCognitionOutputMode,
    ExternalCognitionProviderError,
    ExternalCognitionProviderErrorClass,
    ExternalCognitionProviderErrorNormalization,
    ExternalCognitionProviderKind,
    ExternalCognitionProviderManifest,
    ExternalCognitionReplayOutcome,
    ExternalCognitionReplayRecord,
    ExternalCognitionRequestEnvelope,
    ExternalCognitionRequestIntent,
    ExternalCognitionResponseEnvelope,
    ExternalCognitionRetryPlan,
    ExternalCognitionRetryPolicy,
    ExternalCognitionRouteCandidate,
    ExternalCognitionRouteOutcome,
    ExternalCognitionRoutePlan,
    ExternalCognitionRoutePolicy,
    ExternalCognitionRouteRule,
    ExternalCognitionSession,
    ExternalCognitionSessionPlan,
    ExternalCognitionStructuredOutputSchema,
    ExternalCognitionStructuredOutputValidationResult,
    ExternalCognitionTransientFixtureResponse,
    ExternalCognitionTrustAssessment,
    ExternalCognitionTrustClass,
    ExternalCognitionUncertaintyProjection,
    InMemoryExternalCognitionAuditLedger,
    InMemoryExternalCognitionCircuitBreakerRepository,
    InMemoryExternalCognitionModelRegistry,
    InMemoryExternalCognitionProviderRegistry,
    InMemoryExternalCognitionReplayRepository,
    InMemoryExternalCognitionRequestRepository,
    InMemoryExternalCognitionSessionRepository,
    content_fingerprint,
    ensure_sha256,
    estimate_tokens_from_bytes,
    external_cognition_fingerprint,
    redact_payload_projection,
    utc_now,
    validate_structured_output_value,
)
from aion_brain.model_gateway.provider_adapter import ControlledModelGatewayService


class ControlledExternalCognitionService:
    """AION-246 governed control and evidence plane for deterministic fixtures."""

    def __init__(
        self,
        *,
        provider_registry: InMemoryExternalCognitionProviderRegistry | None = None,
        model_registry: InMemoryExternalCognitionModelRegistry | None = None,
        session_repository: InMemoryExternalCognitionSessionRepository | None = None,
        request_repository: InMemoryExternalCognitionRequestRepository | None = None,
        replay_repository: InMemoryExternalCognitionReplayRepository | None = None,
        circuit_repository: InMemoryExternalCognitionCircuitBreakerRepository | None = None,
        audit_ledger: InMemoryExternalCognitionAuditLedger | None = None,
        fixture_provider: DeterministicExternalCognitionFixtureProvider | None = None,
        existing_model_gateway_service: ControlledModelGatewayService | None = None,
    ) -> None:
        created_at = utc_now()
        providers = default_provider_manifests(created_at)
        provider_registry = provider_registry or InMemoryExternalCognitionProviderRegistry(
            providers
        )
        capabilities = default_model_capability_records(created_at)
        model_registry = model_registry or InMemoryExternalCognitionModelRegistry(
            provider_registry=provider_registry,
            models=default_model_manifests(),
            capabilities=capabilities,
        )
        self.provider_registry = provider_registry
        self.model_registry = model_registry
        self.session_repository = session_repository or InMemoryExternalCognitionSessionRepository()
        self.request_repository = request_repository or InMemoryExternalCognitionRequestRepository()
        self.replay_repository = replay_repository or InMemoryExternalCognitionReplayRepository()
        policy = ExternalCognitionCircuitBreakerPolicy(policy_id="external-cognition-circuit")
        self.circuit_repository = (
            circuit_repository
            or InMemoryExternalCognitionCircuitBreakerRepository(policy)
        )
        self.audit_ledger = audit_ledger or InMemoryExternalCognitionAuditLedger()
        self.fixture_provider = fixture_provider or DeterministicExternalCognitionFixtureProvider(
            default_fixture_records(created_at)
        )
        self.existing_model_gateway_service = (
            existing_model_gateway_service or ControlledModelGatewayService()
        )

    def validate_authorization(
        self, envelope: ExternalCognitionAuthorizationEnvelope
    ) -> ExternalCognitionAuthorizationEnvelope:
        """Validate AION-245-AI-0001."""

        if (
            envelope.program_id != PROGRAM_ID
            or envelope.authorization_transaction_id != AUTHORIZATION_TRANSACTION_ID
            or envelope.formal_closeout_task != FORMAL_CLOSEOUT_TASK
        ):
            raise ValueError("external-cognition authorization mismatch")
        return envelope

    def bind_secure_runtime_component(
        self,
        *,
        secure_runtime_contract_fingerprint: str,
        secure_runtime_session_fingerprint: str,
    ) -> str:
        """Return a fingerprint-only secure-runtime binding projection."""

        return external_cognition_fingerprint(
            {
                "secure_runtime_contract_fingerprint": ensure_sha256(
                    secure_runtime_contract_fingerprint
                ),
                "secure_runtime_session_fingerprint": ensure_sha256(
                    secure_runtime_session_fingerprint
                ),
            }
        )

    def bind_existing_model_gateway_component(
        self,
        *,
        binding_id: str,
        current_main_commit: str,
        secure_runtime_contract_fingerprint: str,
        secure_runtime_session_fingerprint: str,
        existing_model_gateway_contract_fingerprint: str,
        existing_provider_manifest_projection_fingerprint: str,
        existing_model_manifest_projection_fingerprint: str,
        existing_route_policy_projection_fingerprint: str,
        resource_limit_fingerprint: str,
        created_at: datetime,
    ) -> ExternalCognitionComponentBinding:
        """Bind the new control plane to the existing deterministic model gateway."""

        service_fingerprint = external_cognition_fingerprint(
            {
                "service": self.existing_model_gateway_service.__class__.__name__,
                "module": self.existing_model_gateway_service.__class__.__module__,
            }
        )
        return ExternalCognitionComponentBinding(
            binding_id=binding_id,
            current_main_commit=current_main_commit,
            secure_runtime_contract_fingerprint=secure_runtime_contract_fingerprint,
            secure_runtime_session_fingerprint=secure_runtime_session_fingerprint,
            existing_model_gateway_contract_fingerprint=existing_model_gateway_contract_fingerprint,
            existing_model_gateway_service_fingerprint=service_fingerprint,
            existing_provider_manifest_projection_fingerprint=(
                existing_provider_manifest_projection_fingerprint
            ),
            existing_model_manifest_projection_fingerprint=(
                existing_model_manifest_projection_fingerprint
            ),
            existing_route_policy_projection_fingerprint=(
                existing_route_policy_projection_fingerprint
            ),
            resource_limit_fingerprint=resource_limit_fingerprint,
            created_at=created_at,
        )

    def create_session_plan(
        self,
        *,
        session_plan_id: str,
        authorization_envelope: ExternalCognitionAuthorizationEnvelope,
        component_binding: ExternalCognitionComponentBinding,
        created_at: datetime,
        expires_at: datetime,
    ) -> ExternalCognitionSessionPlan:
        """Create a bounded fixture session plan."""

        return ExternalCognitionSessionPlan(
            session_plan_id=session_plan_id,
            authorization_envelope=self.validate_authorization(authorization_envelope),
            component_binding=component_binding,
            created_at=created_at,
            expires_at=expires_at,
        )

    def start_session(self, plan: ExternalCognitionSessionPlan) -> ExternalCognitionSession:
        """Start the only active fixture session."""

        session = self.session_repository.start_session(plan)
        self.record_audit(
            session_id=session.session_id,
            event_type="session_started",
            outcome="accepted",
            created_at=session.created_at,
        )
        return session

    def load_provider_manifests(
        self,
        manifests: Sequence[ExternalCognitionProviderManifest] | None = None,
    ) -> tuple[ExternalCognitionProviderManifest, ...]:
        """Load immutable provider manifests."""

        if manifests is not None:
            self.provider_registry = InMemoryExternalCognitionProviderRegistry(manifests)
        return self.provider_registry.list_manifests()

    def load_model_manifests(
        self,
        models: Sequence[ExternalCognitionModelManifest] | None = None,
        capabilities: Sequence[ExternalCognitionModelCapabilityRecord] | None = None,
    ) -> tuple[ExternalCognitionModelManifest, ...]:
        """Load immutable model manifests and capability records."""

        if models is not None and capabilities is not None:
            self.model_registry = InMemoryExternalCognitionModelRegistry(
                provider_registry=self.provider_registry,
                models=models,
                capabilities=capabilities,
            )
        return self.model_registry.list_models()

    def load_capability_records(
        self,
    ) -> tuple[ExternalCognitionModelCapabilityRecord, ...]:
        """Return immutable capability records."""

        return self.model_registry.list_capabilities()

    def normalize_messages(
        self,
        *,
        messages: Sequence[tuple[str, ExternalCognitionMessageRole | str, str]],
        normalized_at: datetime,
    ) -> tuple[ExternalCognitionMessageProjection, ...]:
        """Normalize transient messages and retain only projections."""

        projections: list[ExternalCognitionMessageProjection] = []
        for message_id, raw_role, content in messages:
            role = ExternalCognitionMessageRole(raw_role)
            byte_count = len(content.encode("utf-8"))
            redaction = redact_payload_projection(
                {"message": content},
                result_id=f"redact-{message_id}",
            )
            projections.append(
                ExternalCognitionMessageProjection(
                    message_id=message_id,
                    role=role,
                    utf8_byte_count=byte_count,
                    deterministic_token_estimate=estimate_tokens_from_bytes(byte_count),
                    content_fingerprint=content_fingerprint("external_cognition_message", content),
                    redaction_finding_count=redaction.finding_count,
                    protected_material_present=redaction.finding_count > 0,
                    normalized_at=normalized_at,
                )
            )
        return tuple(projections)

    def validate_structured_output_schema(
        self, schema: ExternalCognitionStructuredOutputSchema
    ) -> ExternalCognitionStructuredOutputSchema:
        """Validate a restricted structured-output schema."""

        return schema

    def create_request_envelope(
        self,
        *,
        request_id: str,
        session: ExternalCognitionSession,
        authorization: ExternalCognitionAuthorizationEnvelope,
        component_binding: ExternalCognitionComponentBinding,
        request_intent: ExternalCognitionRequestIntent,
        requested_capability_codes: Sequence[ExternalCognitionCapabilityKind],
        messages: Sequence[ExternalCognitionMessageProjection],
        context_budget: ExternalCognitionContextBudget,
        output_budget: ExternalCognitionOutputBudget,
        cost_budget: ExternalCognitionCostBudget,
        latency_budget: ExternalCognitionLatencyBudget,
        route_policy: ExternalCognitionRoutePolicy,
        structured_output_schema: ExternalCognitionStructuredOutputSchema | None,
        safe_metadata: Mapping[str, str],
        created_at: datetime,
        expires_at: datetime,
    ) -> ExternalCognitionRequestEnvelope:
        """Create a fingerprint-only request envelope."""

        request_seed = {
            "request_id": request_id,
            "messages": [item.message_fingerprint for item in messages],
            "intent": request_intent.value,
            "capabilities": [item.value for item in requested_capability_codes],
        }
        return ExternalCognitionRequestEnvelope(
            request_id=request_id,
            session_id=session.session_id,
            authorization_fingerprint=authorization.authorization_fingerprint or "",
            component_binding_fingerprint=component_binding.binding_fingerprint or "",
            request_intent=request_intent,
            requested_capability_codes=tuple(requested_capability_codes),
            message_projection_fingerprints=tuple(
                item.message_fingerprint or "" for item in messages
            ),
            structured_output_schema_fingerprint=(
                structured_output_schema.schema_fingerprint if structured_output_schema else None
            ),
            context_budget_fingerprint=context_budget.budget_fingerprint or "",
            output_budget_fingerprint=output_budget.budget_fingerprint or "",
            cost_budget_fingerprint=cost_budget.budget_fingerprint or "",
            latency_budget_fingerprint=latency_budget.budget_fingerprint or "",
            routing_policy_fingerprint=route_policy.policy_fingerprint or "",
            safe_metadata=safe_metadata,
            idempotency_fingerprint=external_cognition_fingerprint(request_seed),
            created_at=created_at,
            expires_at=expires_at,
        )

    def check_request_replay(
        self, request: ExternalCognitionRequestEnvelope
    ) -> tuple[ExternalCognitionReplayOutcome, str | None]:
        """Check exact replay and reject changed replay before routing."""

        return self.request_repository.check_request_idempotency(request)

    def evaluate_context_budget(
        self,
        *,
        decision_id: str,
        budget: ExternalCognitionContextBudget,
        messages: Sequence[ExternalCognitionMessageProjection],
        created_at: datetime,
    ) -> ExternalCognitionBudgetDecision:
        """Evaluate payload, message, and context-token budgets fail-closed."""

        usage = {
            "message_count": len(messages),
            "payload_bytes": sum(item.utf8_byte_count for item in messages),
            "declared_context_tokens": sum(item.deterministic_token_estimate for item in messages),
        }
        reasons: list[str] = []
        if usage["message_count"] > budget.maximum_messages:
            reasons.append("message_count_exceeded")
        if usage["payload_bytes"] > budget.maximum_payload_bytes:
            reasons.append("request_payload_exceeded")
        if usage["declared_context_tokens"] > budget.maximum_declared_context_tokens:
            reasons.append("context_tokens_exceeded")
        return _budget_decision(
            decision_id=decision_id,
            budget_fingerprint=budget.budget_fingerprint or "",
            usage=usage,
            reasons=reasons,
            created_at=created_at,
        )

    def evaluate_output_budget(
        self,
        *,
        decision_id: str,
        budget: ExternalCognitionOutputBudget,
        requested_output_tokens: int,
        response_payload_bytes: int,
        created_at: datetime,
    ) -> ExternalCognitionBudgetDecision:
        """Evaluate output budget fail-closed."""

        usage = {
            "requested_output_tokens": requested_output_tokens,
            "response_payload_bytes": response_payload_bytes,
        }
        reasons: list[str] = []
        if requested_output_tokens > budget.maximum_output_tokens:
            reasons.append("output_tokens_exceeded")
        if response_payload_bytes > budget.maximum_response_payload_bytes:
            reasons.append("response_payload_exceeded")
        return _budget_decision(
            decision_id=decision_id,
            budget_fingerprint=budget.budget_fingerprint or "",
            usage=usage,
            reasons=reasons,
            created_at=created_at,
        )

    def evaluate_cost_budget(
        self,
        *,
        decision_id: str,
        budget: ExternalCognitionCostBudget,
        declared_cost_units: int,
        created_at: datetime,
    ) -> ExternalCognitionBudgetDecision:
        """Evaluate abstract declared cost budget fail-closed."""

        reasons = (
            ["cost_units_exceeded"]
            if declared_cost_units > budget.maximum_declared_cost_units
            else []
        )
        return _budget_decision(
            decision_id=decision_id,
            budget_fingerprint=budget.budget_fingerprint or "",
            usage={"declared_cost_units": declared_cost_units},
            reasons=reasons,
            created_at=created_at,
        )

    def evaluate_latency_budget(
        self,
        *,
        decision_id: str,
        budget: ExternalCognitionLatencyBudget,
        declared_latency_units: int,
        created_at: datetime,
    ) -> ExternalCognitionBudgetDecision:
        """Evaluate declared latency budget fail-closed."""

        reasons = [
            "latency_units_exceeded"
        ] if declared_latency_units > budget.maximum_declared_latency_units else []
        return _budget_decision(
            decision_id=decision_id,
            budget_fingerprint=budget.budget_fingerprint or "",
            usage={"declared_latency_units": declared_latency_units},
            reasons=reasons,
            created_at=created_at,
        )

    def plan_route(
        self,
        *,
        route_plan_id: str,
        request: ExternalCognitionRequestEnvelope,
        policy: ExternalCognitionRoutePolicy,
        created_at: datetime,
    ) -> ExternalCognitionRoutePlan:
        """Plan a deterministic model route compatible with the existing gateway."""

        candidates: list[ExternalCognitionRouteCandidate] = []
        requested = set(request.requested_capability_codes)
        desired_output_mode = (
            ExternalCognitionOutputMode.structured_json
            if request.structured_output_schema_fingerprint
            else ExternalCognitionOutputMode.text
        )
        for model in self.model_registry.list_models():
            provider = self.provider_registry.get(model.provider_id)
            model_capabilities = self.model_registry.capabilities_for_model(model.model_id)
            capability_set = {item.capability_kind for item in model_capabilities}
            reasons: list[str] = []
            matched_rules = [
                rule
                for rule in policy.rules
                if provider.provider_id in rule.allowed_provider_ids
                and model.model_id in rule.allowed_model_ids
                and requested.issubset(set(rule.required_capabilities))
            ]
            if not matched_rules:
                reasons.append("routing_policy_not_matched")
            for rule in matched_rules:
                if rule.output_mode != desired_output_mode:
                    reasons.append("output_mode_unsupported_by_policy")
                if model.declared_cost_units > rule.maximum_declared_cost_units:
                    reasons.append("declared_cost_units_exceeded")
                if model.declared_latency_units > rule.maximum_declared_latency_units:
                    reasons.append("declared_latency_units_exceeded")
            if not requested.issubset(capability_set):
                reasons.append("missing_required_capability")
            if request.request_intent == ExternalCognitionRequestIntent.long_context:
                if model.declared_context_token_limit < 200_000:
                    reasons.append("context_capacity_insufficient")
            if (
                model.structured_output_supported is False
                and request.structured_output_schema_fingerprint
            ):
                reasons.append("structured_output_unsupported")
            if (
                self.circuit_repository.state_for_model(model.model_id).state
                == ExternalCognitionCircuitState.open
            ):
                reasons.append("circuit_open")
            candidates.append(
                ExternalCognitionRouteCandidate(
                    provider_id=provider.provider_id,
                    model_id=model.model_id,
                    matched_capabilities=tuple(capability_set & requested),
                    output_mode=desired_output_mode,
                    declared_context_tokens=model.declared_context_token_limit,
                    declared_output_tokens=model.declared_output_token_limit,
                    declared_cost_units=model.declared_cost_units,
                    declared_latency_units=model.declared_latency_units,
                    circuit_state=self.circuit_repository.state_for_model(model.model_id).state,
                    rejection_reasons=tuple(reasons),
                )
            )
        candidates = sorted(
            candidates,
            key=lambda item: (bool(item.rejection_reasons), item.model_id),
        )
        selected = next((item for item in candidates if not item.rejection_reasons), None)
        plan_reasons: tuple[str, ...] = (
            ("none",) if selected is not None else ("no_eligible_model",)
        )
        return ExternalCognitionRoutePlan(
            route_plan_id=route_plan_id,
            request_fingerprint=request.request_fingerprint or "",
            policy_fingerprint=policy.policy_fingerprint or "",
            outcome=(
                ExternalCognitionRouteOutcome.selected
                if selected is not None
                else ExternalCognitionRouteOutcome.rejected
            ),
            selected_provider_id=selected.provider_id if selected else None,
            selected_model_id=selected.model_id if selected else None,
            candidates=tuple(candidates),
            rejection_reasons=plan_reasons,
            existing_model_gateway_route_fingerprint=external_cognition_fingerprint(
                {
                    "existing_model_gateway": "compatible",
                    "selected_model_id": selected.model_id if selected else None,
                    "request_fingerprint": request.request_fingerprint,
                }
            ),
            existing_model_gateway_compatible=True,
            created_at=created_at,
        )

    def plan_retry(
        self,
        *,
        retry_plan_id: str,
        request: ExternalCognitionRequestEnvelope,
        policy: ExternalCognitionRetryPolicy,
        error: ExternalCognitionProviderError,
    ) -> ExternalCognitionRetryPlan:
        """Plan bounded retry attempts."""

        attempts = min(MAXIMUM_RETRY_ATTEMPTS, policy.maximum_attempts) if error.retryable else 0
        return ExternalCognitionRetryPlan(
            retry_plan_id=retry_plan_id,
            request_fingerprint=request.request_fingerprint or "",
            policy_fingerprint=policy.policy_fingerprint or "",
            planned_attempts=attempts,
            reason_codes=("retryable_fixture_error",) if attempts else ("retry_not_allowed",),
        )

    def plan_fallback(
        self,
        *,
        fallback_plan_id: str,
        route_plan: ExternalCognitionRoutePlan,
    ) -> ExternalCognitionFallbackPlan:
        """Plan deterministic fallback to a different eligible model."""

        if route_plan.selected_model_id is None:
            return ExternalCognitionFallbackPlan(
                fallback_plan_id=fallback_plan_id,
                primary_model_id="none",
                fallback_model_id=None,
                fallback_eligible=False,
                reason_codes=("no_primary_model",),
            )
        eligible = [
            item.model_id
            for item in route_plan.candidates
            if not item.rejection_reasons and item.model_id != route_plan.selected_model_id
        ]
        return ExternalCognitionFallbackPlan(
            fallback_plan_id=fallback_plan_id,
            primary_model_id=route_plan.selected_model_id,
            fallback_model_id=eligible[0] if eligible else None,
            fallback_eligible=bool(eligible),
            reason_codes=("eligible_fallback_available",) if eligible else ("no_fallback_model",),
        )

    def evaluate_circuit_breaker(
        self,
        *,
        decision_id: str,
        model_id: str,
        record_failure: bool = False,
    ) -> ExternalCognitionCircuitBreakerDecision:
        """Evaluate deterministic circuit state."""

        prior = self.circuit_repository.state_for_model(model_id)
        next_state = (
            self.circuit_repository.record_failure(model_id) if record_failure else prior
        )
        return ExternalCognitionCircuitBreakerDecision(
            decision_id=decision_id,
            prior_state_fingerprint=prior.state_fingerprint or "",
            next_state=next_state,
            allowed=next_state.state != ExternalCognitionCircuitState.open,
            reason_codes=(next_state.state.value,),
        )

    def invoke_deterministic_fixture(
        self,
        *,
        fixture_id: str,
        transient_output: object | None = None,
    ) -> ExternalCognitionTransientFixtureResponse:
        """Invoke a deterministic local fixture provider."""

        return self.fixture_provider.invoke(
            fixture_id=fixture_id,
            transient_output=transient_output,
        )

    def project_response(
        self,
        *,
        response_id: str,
        request: ExternalCognitionRequestEnvelope,
        route_plan: ExternalCognitionRoutePlan,
        fixture_response: ExternalCognitionTransientFixtureResponse,
        trust_assessment: ExternalCognitionTrustAssessment,
        validation: ExternalCognitionStructuredOutputValidationResult | None,
        fallback_plan: ExternalCognitionFallbackPlan | None,
        retry_plan: ExternalCognitionRetryPlan | None,
        created_at: datetime,
    ) -> ExternalCognitionResponseEnvelope:
        """Project transient fixture output into a raw-output-free response envelope."""

        record = fixture_response.fixture_record
        provider = self.provider_registry.get(record.provider_id)
        model = self.model_registry.get_model(record.model_id)
        return ExternalCognitionResponseEnvelope(
            response_id=response_id,
            request_fingerprint=request.request_fingerprint or "",
            provider_manifest_fingerprint=provider.manifest_fingerprint or "",
            model_manifest_fingerprint=model.manifest_fingerprint or "",
            route_plan_fingerprint=route_plan.route_plan_fingerprint or "",
            fallback_plan_fingerprint=fallback_plan.fallback_fingerprint if fallback_plan else None,
            retry_plan_fingerprint=retry_plan.retry_plan_fingerprint if retry_plan else None,
            response_content_fingerprint=content_fingerprint(
                "external_cognition_response",
                str(fixture_response.transient_output),
            ),
            response_byte_count=fixture_response.response_byte_count,
            deterministic_token_usage=record.declared_token_use,
            structured_output_validation_fingerprint=(
                validation.validation_fingerprint if validation else None
            ),
            trust_assessment=trust_assessment,
            uncertainty_projection=record.uncertainty_projection,
            normalized_error=record.normalized_error,
            operator_review_required=trust_assessment.operator_review_required,
            created_at=created_at,
        )

    def validate_structured_response(
        self,
        *,
        validation_id: str,
        schema: ExternalCognitionStructuredOutputSchema,
        transient_output: object,
        created_at: datetime,
    ) -> ExternalCognitionStructuredOutputValidationResult:
        """Validate transient structured output and keep only fingerprints."""

        accepted, reasons = validate_structured_output_value(
            schema.schema_definition,
            transient_output,
        )
        return ExternalCognitionStructuredOutputValidationResult(
            validation_id=validation_id,
            schema_fingerprint=schema.schema_fingerprint or "",
            output_fingerprint=content_fingerprint("structured_output", str(transient_output)),
            accepted=accepted,
            reason_codes=reasons,
            trust_class=(
                ExternalCognitionTrustClass.schema_validated_untrusted
                if accepted
                else ExternalCognitionTrustClass.rejected
            ),
            created_at=created_at,
        )

    def assess_trust(
        self,
        *,
        trust_assessment_id: str,
        validation: ExternalCognitionStructuredOutputValidationResult | None,
        created_at: datetime,
    ) -> ExternalCognitionTrustAssessment:
        """Assess all fixture outputs as untrusted."""

        trust_class = (
            ExternalCognitionTrustClass.schema_validated_untrusted
            if validation and validation.accepted
            else ExternalCognitionTrustClass.untrusted_fixture_output
        )
        if validation and not validation.accepted:
            trust_class = ExternalCognitionTrustClass.rejected
        return ExternalCognitionTrustAssessment(
            trust_assessment_id=trust_assessment_id,
            trust_class=trust_class,
            schema_validation_fingerprint=validation.validation_fingerprint if validation else None,
            operator_review_required=trust_class != ExternalCognitionTrustClass.rejected,
            created_at=created_at,
        )

    def project_uncertainty(
        self,
        *,
        uncertainty_id: str,
        declared_confidence: float,
        operator_review_required: bool,
    ) -> ExternalCognitionUncertaintyProjection:
        """Create explicit uncertainty projection."""

        return ExternalCognitionUncertaintyProjection(
            uncertainty_id=uncertainty_id,
            declared_confidence=declared_confidence,
            confidence_source_code="fixture_declared",
            disagreement_count=0,
            missing_evidence_count=1,
            unresolved_claim_count=1,
            calibration_status_code="uncalibrated_fixture",
            operator_review_required=operator_review_required,
        )

    def normalize_provider_error(
        self,
        *,
        normalization_id: str,
        error_id: str,
        error_class: ExternalCognitionProviderErrorClass,
    ) -> ExternalCognitionProviderErrorNormalization:
        """Normalize provider errors without raw messages."""

        error = ExternalCognitionProviderError(
            error_id=error_id,
            normalized_error_class=error_class,
            retryable=error_class
            in {
                ExternalCognitionProviderErrorClass.timeout,
                ExternalCognitionProviderErrorClass.rate_limited,
                ExternalCognitionProviderErrorClass.unavailable,
                ExternalCognitionProviderErrorClass.internal_error,
            },
            fallback_eligible=True,
            circuit_breaker_effect=ExternalCognitionCircuitState.open,
            safe_error_code=error_class.value,
        )
        return ExternalCognitionProviderErrorNormalization(
            normalization_id=normalization_id,
            input_error_fingerprint=external_cognition_fingerprint(
                {"safe_error_class": error_class.value}
            ),
            normalized_error=error,
        )

    def create_operator_review(
        self,
        *,
        review_id: str,
        response: ExternalCognitionResponseEnvelope,
        reason_codes: Sequence[str],
        created_at: datetime,
    ) -> ExternalCognitionOperatorReviewRecord:
        """Create operator-review record with no raw output."""

        return ExternalCognitionOperatorReviewRecord(
            review_id=review_id,
            response_fingerprint=response.response_fingerprint or "",
            trust_class=response.trust_assessment.trust_class,
            reason_codes=tuple(reason_codes),
            created_at=created_at,
        )

    def record_audit(
        self,
        *,
        session_id: str,
        event_type: str,
        outcome: str,
        created_at: datetime,
        subject_fingerprint: str = ZERO_FINGERPRINT,
    ) -> object:
        """Append a redacted audit record."""

        return self.audit_ledger.append(
            session_id=session_id,
            event_type=event_type,
            outcome=outcome,
            subject_fingerprint=subject_fingerprint,
            created_at=created_at,
        )

    def create_observability_snapshot(
        self,
        *,
        snapshot_id: str,
        session_id: str,
        counters: Mapping[str, int],
        trust_class_counts: Mapping[str, int],
        uncertainty_counts: Mapping[str, int],
        circuit_states: Mapping[str, str],
        evidence_chain_head: str,
        created_at: datetime,
    ) -> ExternalCognitionObservabilitySnapshot:
        """Create redacted observability snapshot."""

        return ExternalCognitionObservabilitySnapshot(
            snapshot_id=snapshot_id,
            session_id=session_id,
            counters=counters,
            trust_class_counts=trust_class_counts,
            uncertainty_counts=uncertainty_counts,
            circuit_states=circuit_states,
            audit_chain_head=self.audit_ledger.chain_head(session_id),
            evidence_chain_head=evidence_chain_head,
            created_at=created_at,
        )

    def audit_integrity(
        self,
        *,
        report_id: str,
        session_id: str,
        evidence_chain_head: str,
        prohibited_effect_counters: Mapping[str, int],
        created_at: datetime,
    ) -> ExternalCognitionIntegrityReport:
        """Audit integrity and zero prohibited effects."""

        categories = (
            "authorization_lineage",
            "component_lineage",
            "manifest_referential_integrity",
            "budget_integrity",
            "route_determinism",
            "replay_integrity",
            "circuit_breaker_integrity",
            "trust_integrity",
            "redaction_integrity",
            "audit_chain_integrity",
            "evidence_chain_integrity",
            "zero_prohibited_effects",
        )
        findings = tuple(
            key for key, value in prohibited_effect_counters.items() if value != 0
        )
        return ExternalCognitionIntegrityReport(
            report_id=report_id,
            status=(
                ExternalCognitionIntegrityStatus.failed
                if findings
                else ExternalCognitionIntegrityStatus.passed
            ),
            checked_categories=categories,
            finding_codes=findings,
            prohibited_effect_counters=prohibited_effect_counters,
            audit_chain_head=self.audit_ledger.chain_head(session_id),
            evidence_chain_head=evidence_chain_head,
            created_at=created_at,
        )

    def create_evidence_bundle(
        self,
        *,
        evidence_id: str,
        session_id: str,
        observability: ExternalCognitionObservabilitySnapshot,
        integrity: ExternalCognitionIntegrityReport,
        counters: Mapping[str, int],
        prohibited_effect_counters: Mapping[str, int],
        evidence_chain_head: str,
        created_at: datetime,
    ) -> ExternalCognitionEvidenceBundle:
        """Create redacted evidence bundle."""

        return ExternalCognitionEvidenceBundle(
            evidence_id=evidence_id,
            session_id=session_id,
            audit_chain_head=self.audit_ledger.chain_head(session_id),
            evidence_chain_head=evidence_chain_head,
            observability_fingerprint=observability.snapshot_fingerprint or "",
            integrity_report_fingerprint=integrity.report_fingerprint or "",
            counters=counters,
            prohibited_effect_counters=prohibited_effect_counters,
            created_at=created_at,
        )

    def replay_exact_request(
        self,
        *,
        request: ExternalCognitionRequestEnvelope,
        safe_response_fingerprint: str,
        created_at: datetime,
    ) -> ExternalCognitionReplayRecord:
        """Return exact replay without invoking a fixture again."""

        return self.replay_repository.observe(
            request=request,
            safe_response_fingerprint=safe_response_fingerprint,
            created_at=created_at,
        )

    def reject_changed_replay(
        self,
        *,
        request: ExternalCognitionRequestEnvelope,
        safe_response_fingerprint: str,
        created_at: datetime,
    ) -> ExternalCognitionReplayRecord:
        """Reject changed replay before routing or fixture invocation."""

        return self.replay_repository.observe(
            request=request,
            safe_response_fingerprint=safe_response_fingerprint,
            created_at=created_at,
        )

    def close_session(self, *, session_id: str, closed_at: datetime) -> ExternalCognitionSession:
        """Close a fixture session."""

        session = self.session_repository.close_session(session_id, closed_at)
        self.record_audit(
            session_id=session_id,
            event_type="session_closed",
            outcome="closed",
            created_at=closed_at,
        )
        return session


def _budget_decision(
    *,
    decision_id: str,
    budget_fingerprint: str,
    usage: Mapping[str, int],
    reasons: Sequence[str],
    created_at: datetime,
) -> ExternalCognitionBudgetDecision:
    reason_codes = tuple(reasons) if reasons else ("passed",)
    return ExternalCognitionBudgetDecision(
        decision_id=decision_id,
        budget_fingerprint=budget_fingerprint,
        usage_fingerprint=external_cognition_fingerprint(usage),
        outcome=(
            ExternalCognitionBudgetOutcome.rejected
            if reasons
            else ExternalCognitionBudgetOutcome.passed
        ),
        reason_codes=reason_codes,
        created_at=created_at,
    )


def default_provider_manifests(
    created_at: datetime,
) -> tuple[ExternalCognitionProviderManifest, ...]:
    """Return the three canonical deterministic fixture providers."""

    provider_ids = ("fixture-provider-alpha", "fixture-provider-beta", "fixture-provider-gamma")
    capabilities = tuple(ExternalCognitionCapabilityKind)
    modes = (ExternalCognitionOutputMode.structured_json, ExternalCognitionOutputMode.text)
    return tuple(
        ExternalCognitionProviderManifest(
            provider_id=provider_id,
            provider_kind=ExternalCognitionProviderKind.deterministic_fixture,
            provider_display_code=provider_id,
            supported_output_modes=modes,
            supported_capability_codes=capabilities,
            declared_availability_class="fixture_available",
            declared_cost_class_code=f"cost_class_{index}",
            declared_latency_class_code=f"latency_class_{index}",
            created_at=created_at,
        )
        for index, provider_id in enumerate(provider_ids, start=1)
    )


def default_model_capability_records(
    created_at: datetime,
) -> tuple[ExternalCognitionModelCapabilityRecord, ...]:
    """Return the canonical eighteen capability records."""

    del created_at
    model_capabilities: dict[str, tuple[ExternalCognitionCapabilityKind, ...]] = {
        "fixture-reasoner-large-v1": (
            ExternalCognitionCapabilityKind.general_reasoning,
            ExternalCognitionCapabilityKind.fact_verification,
            ExternalCognitionCapabilityKind.long_context,
        ),
        "fixture-reasoner-small-v1": (
            ExternalCognitionCapabilityKind.general_reasoning,
            ExternalCognitionCapabilityKind.classification,
            ExternalCognitionCapabilityKind.summarization,
        ),
        "fixture-code-v1": (
            ExternalCognitionCapabilityKind.code_reasoning,
            ExternalCognitionCapabilityKind.general_reasoning,
            ExternalCognitionCapabilityKind.summarization,
        ),
        "fixture-structured-v1": (
            ExternalCognitionCapabilityKind.structured_extraction,
            ExternalCognitionCapabilityKind.restricted_structured_output,
            ExternalCognitionCapabilityKind.classification,
        ),
        "fixture-long-context-v1": (
            ExternalCognitionCapabilityKind.long_context,
            ExternalCognitionCapabilityKind.general_reasoning,
            ExternalCognitionCapabilityKind.fact_verification,
        ),
        "fixture-multilingual-v1": (
            ExternalCognitionCapabilityKind.multilingual_reasoning,
            ExternalCognitionCapabilityKind.general_reasoning,
            ExternalCognitionCapabilityKind.summarization,
        ),
    }
    provider_by_model = {
        "fixture-reasoner-large-v1": "fixture-provider-alpha",
        "fixture-reasoner-small-v1": "fixture-provider-alpha",
        "fixture-code-v1": "fixture-provider-beta",
        "fixture-structured-v1": "fixture-provider-beta",
        "fixture-long-context-v1": "fixture-provider-gamma",
        "fixture-multilingual-v1": "fixture-provider-gamma",
    }
    records: list[ExternalCognitionModelCapabilityRecord] = []
    for model_id, capabilities in model_capabilities.items():
        for capability in capabilities:
            records.append(
                ExternalCognitionModelCapabilityRecord(
                    capability_record_id=f"{model_id}-{capability.value}",
                    provider_id=provider_by_model[model_id],
                    model_id=model_id,
                    capability_kind=capability,
                    output_modes=(
                        ExternalCognitionOutputMode.structured_json,
                        ExternalCognitionOutputMode.text,
                    )
                    if capability
                    in {
                        ExternalCognitionCapabilityKind.structured_extraction,
                        ExternalCognitionCapabilityKind.restricted_structured_output,
                    }
                    else (ExternalCognitionOutputMode.text,),
                    declared_context_tokens=(
                        500_000
                        if capability == ExternalCognitionCapabilityKind.long_context
                        else 200_000
                    ),
                    declared_output_tokens=8_192,
                    structured_output_supported=capability
                    in {
                        ExternalCognitionCapabilityKind.structured_extraction,
                        ExternalCognitionCapabilityKind.restricted_structured_output,
                    },
                )
            )
    return tuple(records)


def default_model_manifests() -> tuple[ExternalCognitionModelManifest, ...]:
    """Return the six canonical deterministic fixture model manifests."""

    model_defs = (
        ("fixture-reasoner-large-v1", "fixture-provider-alpha", "reasoner", 500_000, 12, 9),
        ("fixture-reasoner-small-v1", "fixture-provider-alpha", "reasoner", 200_000, 4, 4),
        ("fixture-code-v1", "fixture-provider-beta", "code", 200_000, 5, 5),
        ("fixture-structured-v1", "fixture-provider-beta", "structured", 200_000, 4, 4),
        ("fixture-long-context-v1", "fixture-provider-gamma", "long_context", 1_000_000, 8, 8),
        ("fixture-multilingual-v1", "fixture-provider-gamma", "multilingual", 200_000, 4, 5),
    )
    return tuple(
        ExternalCognitionModelManifest(
            model_id=model_id,
            provider_id=provider_id,
            model_family_code=family,
            model_version_code="v1",
            capability_record_ids=tuple(
                record.capability_record_id
                for record in default_model_capability_records(utc_now())
                if record.model_id == model_id
            ),
            declared_context_token_limit=context_limit,
            declared_output_token_limit=8_192,
            declared_cost_units=cost_units,
            declared_latency_units=latency_units,
            structured_output_supported=model_id == "fixture-structured-v1",
        )
        for model_id, provider_id, family, context_limit, cost_units, latency_units in model_defs
    )


def default_route_policies() -> tuple[ExternalCognitionRoutePolicy, ...]:
    """Return six canonical route policies."""

    rules = (
        (
            "reasoning-policy",
            ExternalCognitionCapabilityKind.general_reasoning,
            ("fixture-reasoner-large-v1", "fixture-reasoner-small-v1"),
            ExternalCognitionOutputMode.text,
        ),
        (
            "code-policy",
            ExternalCognitionCapabilityKind.code_reasoning,
            ("fixture-code-v1",),
            ExternalCognitionOutputMode.text,
        ),
        (
            "structured-policy",
            ExternalCognitionCapabilityKind.structured_extraction,
            ("fixture-structured-v1",),
            ExternalCognitionOutputMode.structured_json,
        ),
        (
            "long-context-policy",
            ExternalCognitionCapabilityKind.long_context,
            ("fixture-long-context-v1", "fixture-reasoner-large-v1"),
            ExternalCognitionOutputMode.text,
        ),
        (
            "multilingual-policy",
            ExternalCognitionCapabilityKind.multilingual_reasoning,
            ("fixture-multilingual-v1",),
            ExternalCognitionOutputMode.text,
        ),
        (
            "fallback-policy",
            ExternalCognitionCapabilityKind.general_reasoning,
            ("fixture-reasoner-small-v1", "fixture-code-v1"),
            ExternalCognitionOutputMode.text,
        ),
    )
    return tuple(
        ExternalCognitionRoutePolicy(
            policy_id=policy_id,
            rules=(
                ExternalCognitionRouteRule(
                    rule_id=f"{policy_id}-rule",
                    allowed_provider_ids=(
                        "fixture-provider-alpha",
                        "fixture-provider-beta",
                        "fixture-provider-gamma",
                    ),
                    allowed_model_ids=model_ids,
                    required_capabilities=(capability,),
                    output_mode=mode,
                    maximum_declared_cost_units=100,
                    maximum_declared_latency_units=100,
                ),
            ),
        )
        for policy_id, capability, model_ids, mode in rules
    )


def default_structured_output_schemas() -> tuple[ExternalCognitionStructuredOutputSchema, ...]:
    """Return the two canonical restricted structured-output schemas."""

    extraction_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "label": {"type": "string", "minLength": 1, "maxLength": 32},
            "score": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["label", "score"],
    }
    classification_schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "category": {
                "type": "string",
                "enum": ["general", "code", "structured", "long_context"],
            }
        },
        "required": ["category"],
    }
    return (
        ExternalCognitionStructuredOutputSchema(
            schema_id="fixture-structured-extraction-schema",
            schema_definition=extraction_schema,
            schema_depth=3,
            property_count=2,
        ),
        ExternalCognitionStructuredOutputSchema(
            schema_id="fixture-classification-schema",
            schema_definition=classification_schema,
            schema_depth=3,
            property_count=1,
        ),
    )


def default_fixture_records(
    created_at: datetime,
) -> tuple[ExternalCognitionFixtureRecord, ...]:
    """Return deterministic fixture records."""

    del created_at
    uncertainty = ExternalCognitionUncertaintyProjection(
        uncertainty_id="fixture-default-uncertainty",
        declared_confidence=0.42,
        confidence_source_code="fixture_declared",
        disagreement_count=0,
        missing_evidence_count=1,
        unresolved_claim_count=1,
        calibration_status_code="uncalibrated_fixture",
        operator_review_required=True,
    )
    entries = (
        (
            "fixture-general",
            ExternalCognitionRequestIntent.reasoning,
            ExternalCognitionCapabilityKind.general_reasoning,
            "fixture-provider-alpha",
            "fixture-reasoner-large-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-code",
            ExternalCognitionRequestIntent.code,
            ExternalCognitionCapabilityKind.code_reasoning,
            "fixture-provider-beta",
            "fixture-code-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-classification",
            ExternalCognitionRequestIntent.classification,
            ExternalCognitionCapabilityKind.classification,
            "fixture-provider-alpha",
            "fixture-reasoner-small-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-summarization",
            ExternalCognitionRequestIntent.summarization,
            ExternalCognitionCapabilityKind.summarization,
            "fixture-provider-alpha",
            "fixture-reasoner-small-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-structured",
            ExternalCognitionRequestIntent.extraction,
            ExternalCognitionCapabilityKind.structured_extraction,
            "fixture-provider-beta",
            "fixture-structured-v1",
            ExternalCognitionOutputMode.structured_json,
        ),
        (
            "fixture-long-context",
            ExternalCognitionRequestIntent.long_context,
            ExternalCognitionCapabilityKind.long_context,
            "fixture-provider-gamma",
            "fixture-long-context-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-multilingual",
            ExternalCognitionRequestIntent.multilingual,
            ExternalCognitionCapabilityKind.multilingual_reasoning,
            "fixture-provider-gamma",
            "fixture-multilingual-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-fallback",
            ExternalCognitionRequestIntent.reasoning,
            ExternalCognitionCapabilityKind.general_reasoning,
            "fixture-provider-alpha",
            "fixture-reasoner-small-v1",
            ExternalCognitionOutputMode.text,
        ),
        (
            "fixture-malformed-structured",
            ExternalCognitionRequestIntent.extraction,
            ExternalCognitionCapabilityKind.structured_extraction,
            "fixture-provider-beta",
            "fixture-structured-v1",
            ExternalCognitionOutputMode.structured_json,
        ),
    )
    return tuple(
        ExternalCognitionFixtureRecord(
            fixture_id=fixture_id,
            request_intent=intent,
            required_capability=capability,
            provider_id=provider_id,
            model_id=model_id,
            response_mode=mode,
            transient_fixture_result_code=f"{fixture_id}-result",
            declared_token_use=128,
            declared_cost_units=3,
            declared_latency_units=3,
            trust_class=ExternalCognitionTrustClass.untrusted_fixture_output,
            uncertainty_projection=uncertainty,
        )
        for fixture_id, intent, capability, provider_id, model_id, mode in entries
    )


def default_budgets() -> tuple[
    ExternalCognitionContextBudget,
    ExternalCognitionOutputBudget,
    ExternalCognitionCostBudget,
    ExternalCognitionLatencyBudget,
    ExternalCognitionRetryPolicy,
    ExternalCognitionCircuitBreakerPolicy,
]:
    """Return canonical budget and policy records."""

    return (
        ExternalCognitionContextBudget(),
        ExternalCognitionOutputBudget(),
        ExternalCognitionCostBudget(),
        ExternalCognitionLatencyBudget(),
        ExternalCognitionRetryPolicy(policy_id="external-cognition-retry-policy"),
        ExternalCognitionCircuitBreakerPolicy(policy_id="external-cognition-circuit-policy"),
    )


def create_default_authorization(
    *,
    session_id: str = "external-cognition-fixture-session",
    operator_identity_fingerprint: str = ZERO_FINGERPRINT,
    created_at: datetime | None = None,
) -> ExternalCognitionAuthorizationEnvelope:
    """Create the canonical AION-245-AI-0001 authorization envelope."""

    started = created_at or utc_now()
    return ExternalCognitionAuthorizationEnvelope(
        session_id=session_id,
        operator_identity_fingerprint=operator_identity_fingerprint,
        created_at=started,
        expires_at=started + timedelta(hours=1),
    )


def create_default_component_binding(
    *,
    current_main_commit: str,
    created_at: datetime | None = None,
) -> ExternalCognitionComponentBinding:
    """Create a canonical component binding for fixtures and examples."""

    now = created_at or utc_now()
    fingerprint = external_cognition_fingerprint({"component": "external-cognition"})
    service = ControlledExternalCognitionService()
    return service.bind_existing_model_gateway_component(
        binding_id="external-cognition-component-binding",
        current_main_commit=current_main_commit,
        secure_runtime_contract_fingerprint=fingerprint,
        secure_runtime_session_fingerprint=fingerprint,
        existing_model_gateway_contract_fingerprint=fingerprint,
        existing_provider_manifest_projection_fingerprint=fingerprint,
        existing_model_manifest_projection_fingerprint=fingerprint,
        existing_route_policy_projection_fingerprint=fingerprint,
        resource_limit_fingerprint=external_cognition_fingerprint(PROHIBITED_EFFECT_COUNTERS),
        created_at=now,
    )
