"""AION Model Gateway service."""

from datetime import UTC, datetime
from typing import cast
from uuid import uuid4

from aion_brain.approvals.integration import evaluate_approval_gate
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.autonomy import AutonomyDecisionRequest
from aion_brain.contracts.model_gateway import (
    ModelBudgetRecord,
    ModelGatewayRequest,
    ModelGatewayResponse,
    ModelGatewayStatus,
    ModelProfile,
    ModelProvider,
    ModelUsageRecord,
    PromptRedactionRecord,
)
from aion_brain.contracts.observability import ObservabilityEvent, ObservabilityLevel
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.model_gateway.budget import ModelBudgetGuard
from aion_brain.model_gateway.profile_registry import (
    DETERMINISTIC_MODEL_NAME,
    ModelProfileRegistry,
    deterministic_profile,
)
from aion_brain.model_gateway.provider_registry import (
    DETERMINISTIC_PROVIDER_ID,
    ModelProviderRegistry,
    deterministic_provider,
)
from aion_brain.model_gateway.redaction import PromptRedactor
from aion_brain.model_gateway.repository import ModelGatewayRepository
from aion_brain.model_gateway.router import ModelGatewayRouter
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import PolicyInputEnricher
from aion_brain.reasoning.base import ModelGatewayAdapter


class ModelGatewayService:
    """Policy-gated model gateway with redaction, budgets, and fallback."""

    def __init__(
        self,
        *,
        provider_registry: ModelProviderRegistry,
        profile_registry: ModelProfileRegistry,
        router: ModelGatewayRouter,
        redactor: PromptRedactor,
        budget_guard: ModelBudgetGuard,
        adapters: dict[str, ModelGatewayAdapter],
        policy_adapter: PolicyAdapter,
        repository: ModelGatewayRepository,
        telemetry_service: object | None = None,
        observability_service: object | None = None,
        model_gateway_enabled: bool = False,
        approval_service: object | None = None,
        autonomy_governor: object | None = None,
        circuit_breaker_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._provider_registry = provider_registry
        self._profile_registry = profile_registry
        self._router = router
        self._redactor = redactor
        self._budget_guard = budget_guard
        self._adapters = adapters
        self._policy_adapter = policy_adapter
        self._repository = repository
        self._telemetry_service = telemetry_service
        self._observability_service = observability_service
        self._model_gateway_enabled = model_gateway_enabled
        self._approval_service = approval_service
        self._autonomy_governor = autonomy_governor
        self._circuit_breaker_service = circuit_breaker_service
        self._audit_sink = audit_sink

    def set_circuit_breaker_service(self, circuit_breaker_service: object | None) -> None:
        """Attach circuit breaker service after kernel assembly."""
        self._circuit_breaker_service = circuit_breaker_service

    def set_audit_sink(self, audit_sink: object | None) -> None:
        """Attach audit sink after kernel assembly."""
        self._audit_sink = audit_sink

    def complete(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        """Complete a prompt through the selected provider boundary."""
        self._emit("model_gateway_requested", "model", request.request_id, 0.4, {})
        gateway_decision = self._authorize(
            request,
            "model.gateway.complete",
            "model_gateway",
            request.request_id,
            {},
        )
        if not gateway_decision:
            return self._blocked_response(request, "blocked_by_policy", "model_gateway_denied")

        try:
            route, provider, profile = self._route(request)
        except LookupError:
            return self._blocked_response(
                request,
                "provider_unavailable",
                "model_provider_unavailable",
            )

        autonomy = self._autonomy_decision(request, provider)
        if autonomy is not None and not bool(getattr(autonomy, "allow", False)):
            return self._blocked_response(
                request,
                "blocked_by_policy",
                str(getattr(autonomy, "reason", "autonomy_denied")),
                route=route,
                provider=provider,
                profile=profile,
            )

        if not self._authorize(
            request,
            "model.route",
            "model_route",
            route.route_id,
            _policy_context(provider, profile, request),
        ):
            return self._blocked_response(
                request,
                "blocked_by_policy",
                "model_route_denied",
                route=route,
                provider=provider,
                profile=profile,
            )
        self._emit(
            "model_route_selected",
            "model",
            route.selected_model,
            0.6,
            {"provider_id": provider.provider_id, "model_profile_id": profile.model_profile_id},
        )
        record_audit_event(
            self._audit_sink,
            action_type="model.route",
            resource_type="model_route",
            resource_id=route.route_id,
            event_type="model_route_selected",
            outcome="allowed",
            source_component="model_gateway",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level=request.risk_level,
            payload={
                "provider_id": provider.provider_id,
                "model_profile_id": profile.model_profile_id,
                "model": route.selected_model,
            },
        )

        redacted_prompt, redaction = self._redactor.redact(request.prompt)
        redaction = redaction.model_copy(update={"reasoning_id": request.reasoning_id})
        if redaction.redaction_count:
            self._repository.save_redaction(redaction)
            self._emit(
                "prompt_redaction_recorded",
                "prompt",
                redaction.redaction_id,
                0.8 if redaction.blocked else 0.4,
                {"blocked": redaction.blocked},
            )
        if redaction.blocked:
            record_audit_event(
                self._audit_sink,
                action_type="model.complete",
                resource_type="model_call",
                resource_id=request.request_id,
                event_type="prompt_redaction_recorded",
                outcome="blocked",
                source_component="model_gateway",
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                risk_level=request.risk_level,
                payload={
                    "redaction_id": redaction.redaction_id,
                    "blocked": True,
                    "reason": redaction.reason or "redaction_blocked",
                },
            )
            return self._blocked_response(
                request,
                "blocked_by_redaction",
                redaction.reason or "secret_like_content_detected",
                route=route,
                provider=provider,
                profile=profile,
                redaction=redaction,
            )

        budget = self._budget_guard.authorize_budget(request, profile)
        if budget is None:
            return self._blocked_response(
                request,
                "blocked_by_budget",
                "model_budget_exceeded",
                route=route,
                provider=provider,
                profile=profile,
                redaction=redaction,
            )
        self._emit("model_budget_checked", "budget", budget.budget_id, 0.7, {})

        if not self._authorize(
            request,
            "model.complete",
            "model_call",
            None,
            _policy_context(provider, profile, request),
        ):
            return self._blocked_response(
                request,
                "blocked_by_policy",
                "model_complete_denied",
                route=route,
                provider=provider,
                profile=profile,
                redaction=redaction,
                budget=budget,
            )

        if request.allow_external and provider.provider_id != DETERMINISTIC_PROVIDER_ID:
            gate = evaluate_approval_gate(
                self._approval_service,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                action_type="model.complete",
                resource_type="model_call",
                resource_id=request.request_id,
                requested_risk_level=request.risk_level,
                security_scope=request.scope,
                payload={"request_id": request.request_id, "provider_id": provider.provider_id},
                context={
                    "approval_present": bool(request.metadata.get("approval_present")),
                    "uses_external_model": True,
                    "external_effect_possible": True,
                    "allow_external": True,
                },
                metadata=request.metadata,
            )
            if gate is not None and gate.final_decision != "allow":
                return self._blocked_response(
                    request,
                    "blocked_by_policy",
                    gate.reason if gate.final_decision == "block" else "approval_required",
                    route=route,
                    provider=provider,
                    profile=profile,
                    redaction=redaction,
                    budget=budget,
                )

        if provider.provider_id != DETERMINISTIC_PROVIDER_ID and not self._allow_external_call():
            return self._blocked_response(
                request,
                "provider_unavailable",
                "circuit_breaker_open",
                route=route,
                provider=provider,
                profile=profile,
                redaction=redaction,
                budget=budget,
            )

        model_call = self._call_adapter(redacted_prompt, route, provider)
        status: ModelGatewayStatus = "completed" if model_call.status == "completed" else "failed"
        reason = None if status == "completed" else model_call.response.get("reason")
        if provider.provider_id != DETERMINISTIC_PROVIDER_ID:
            self._record_external_breaker(status == "completed", reason)
        if status == "failed" and provider.provider_id != DETERMINISTIC_PROVIDER_ID:
            fallback = self._fallback(request, redacted_prompt)
            if fallback is not None:
                route, provider, profile, model_call = fallback
                status = "fallback_used"
                reason = "deterministic_fallback_used"

        usage = self._usage_from_call(request, provider, profile, model_call, status)
        usage = self._budget_guard.record_usage(usage)
        self._emit(
            "model_call_recorded",
            "model",
            model_call.model_call_id,
            0.6,
            {"status": model_call.status, "provider_id": provider.provider_id},
        )
        self._emit(
            "model_usage_recorded",
            "model",
            usage.usage_id,
            0.6,
            {"cost_estimate": usage.cost_estimate},
        )
        record_audit_event(
            self._audit_sink,
            action_type="model.complete",
            resource_type="model_call",
            resource_id=model_call.model_call_id,
            event_type="model_call_recorded",
            outcome="completed" if status in {"completed", "fallback_used"} else "failed",
            source_component="model_gateway",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level=request.risk_level,
            payload={
                "provider_id": provider.provider_id,
                "model": profile.model_name,
                "status": status,
                "usage_id": usage.usage_id,
            },
        )
        response = ModelGatewayResponse(
            request_id=request.request_id,
            model_call=model_call,
            usage=usage,
            redaction=redaction if redaction.redaction_count else None,
            route_decision=route,
            output=model_call.response,
            status=status,
            reason=reason,
            created_at=datetime.now(UTC),
        )
        self._observe(request, response)
        return response

    def _route(
        self,
        request: ModelGatewayRequest,
    ) -> tuple[ModelRouteDecision, ModelProvider, ModelProfile]:
        self._provider_registry.ensure_defaults()
        self._profile_registry.ensure_defaults()
        return self._router.route(
            request,
            self._provider_registry.list_providers(actor_context=_actor_context(request)),
            self._profile_registry.list_profiles(actor_context=_actor_context(request)),
            gateway_enabled=self._model_gateway_enabled,
        )

    def _call_adapter(
        self,
        prompt: object,
        route: ModelRouteDecision,
        provider: ModelProvider,
    ) -> ModelCallRecord:
        adapter = self._adapters.get(provider.provider_type)
        if adapter is None:
            return _failed_call(route, "model_adapter_unavailable")
        try:
            return adapter.complete(prompt, route)  # type: ignore[arg-type]
        except Exception:
            return _failed_call(route, "model_adapter_failed")

    def _allow_external_call(self) -> bool:
        allow_call = getattr(self._circuit_breaker_service, "allow_call", None)
        if not callable(allow_call):
            return True
        try:
            return bool(allow_call("model_gateway"))
        except Exception:
            return True

    def _record_external_breaker(self, success: bool, reason: object | None) -> None:
        method_name = "record_success" if success else "record_failure"
        method = getattr(self._circuit_breaker_service, method_name, None)
        if not callable(method):
            return
        try:
            if success:
                method("model_gateway")
            else:
                method("model_gateway", str(reason or "model_gateway_failed"))
        except Exception:
            return

    def _fallback(
        self,
        request: ModelGatewayRequest,
        prompt: object,
    ) -> tuple[ModelRouteDecision, ModelProvider, ModelProfile, ModelCallRecord] | None:
        provider = deterministic_provider()
        profile = deterministic_profile()
        route = ModelRouteDecision(
            route_id=f"route-fallback-{request.request_id}",
            trace_id=request.trace_id,
            reasoning_id=request.reasoning_id,
            selected_provider=provider.provider_id,
            selected_model=profile.model_name,
            mode=request.mode,
            reason="deterministic_fallback",
            fallback_providers=[],
            privacy_level="local",
            risk_level=request.risk_level,
            estimated_cost=0.0,
            estimated_latency_ms=0,
            created_at=datetime.now(UTC),
        )
        adapter = self._adapters.get(provider.provider_type)
        if adapter is None:
            return None
        try:
            model_call = adapter.complete(prompt, route)  # type: ignore[arg-type]
        except Exception:
            return None
        if model_call.status != "completed":
            return None
        return route, provider, profile, model_call

    def _usage_from_call(
        self,
        request: ModelGatewayRequest,
        provider: ModelProvider,
        profile: ModelProfile,
        model_call: ModelCallRecord,
        gateway_status: str,
    ) -> ModelUsageRecord:
        input_tokens = self._budget_guard.estimate_prompt_tokens(request.prompt)
        output_tokens = self._budget_guard.estimate_tokens(str(model_call.response))
        cost = self._budget_guard.estimate_cost(input_tokens, output_tokens, profile)
        return ModelUsageRecord(
            usage_id=f"usage-{uuid4().hex}",
            trace_id=request.trace_id,
            reasoning_id=request.reasoning_id,
            model_call_id=model_call.model_call_id,
            provider_id=provider.provider_id,
            model_profile_id=profile.model_profile_id,
            model_name=profile.model_name,
            mode=request.mode,
            input_token_estimate=input_tokens,
            output_token_estimate=output_tokens,
            cost_estimate=cost,
            latency_ms=model_call.latency_ms,
            status="recorded" if gateway_status in {"completed", "fallback_used"} else "failed",
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            created_at=datetime.now(UTC),
        )

    def _blocked_response(
        self,
        request: ModelGatewayRequest,
        status: ModelGatewayStatus,
        reason: str,
        *,
        route: ModelRouteDecision | None = None,
        provider: ModelProvider | None = None,
        profile: ModelProfile | None = None,
        redaction: PromptRedactionRecord | None = None,
        budget: ModelBudgetRecord | None = None,
    ) -> ModelGatewayResponse:
        provider = provider or deterministic_provider()
        profile = profile or deterministic_profile()
        route = route or _safe_route(request)
        model_call = _blocked_call(request, route, reason)
        usage = self._budget_guard.record_usage(
            ModelUsageRecord(
                usage_id=f"usage-{uuid4().hex}",
                trace_id=request.trace_id,
                reasoning_id=request.reasoning_id,
                model_call_id=model_call.model_call_id,
                provider_id=provider.provider_id,
                model_profile_id=profile.model_profile_id,
                model_name=profile.model_name,
                mode=request.mode,
                input_token_estimate=self._budget_guard.estimate_prompt_tokens(request.prompt),
                output_token_estimate=0,
                cost_estimate=0.0,
                latency_ms=0,
                status="blocked",
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                created_at=datetime.now(UTC),
            )
        )
        self._emit("model_gateway_blocked", "model", request.request_id, 0.9, {"reason": reason})
        if budget is not None:
            self._emit("model_budget_checked", "budget", budget.budget_id, 0.7, {})
        response = ModelGatewayResponse(
            request_id=request.request_id,
            model_call=model_call,
            usage=usage,
            redaction=redaction,
            route_decision=route,
            output=model_call.response,
            status=status,
            reason=reason,
            created_at=datetime.now(UTC),
        )
        self._observe(request, response)
        return response

    def _authorize(
        self,
        request: ModelGatewayRequest,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        context: dict[str, object],
    ) -> bool:
        actor_context = _actor_context(request)
        decision = self._policy_adapter.authorize(
            PolicyInputEnricher().enrich(
                PolicyRequest(
                    request_id=f"{action_type}-{uuid4().hex}",
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    action_type=action_type,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    risk_level=request.risk_level,
                    approval_present=bool(request.metadata.get("approval_present")),
                    requested_permissions=[],
                    security_scope=request.scope,
                    context={
                        **context,
                        "allow_external": request.allow_external,
                        "model_gateway_enabled": self._model_gateway_enabled,
                    },
                ),
                actor_context,
            )
        )
        return decision.allow

    def _autonomy_decision(
        self,
        request: ModelGatewayRequest,
        provider: ModelProvider,
    ) -> object | None:
        decide = getattr(self._autonomy_governor, "decide", None)
        if not callable(decide):
            return None
        return cast(
            object,
            decide(
                AutonomyDecisionRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    requested_mode="assist" if not request.allow_external else "dry_run",
                    action_type="model.complete",
                    resource_type="model_call",
                    resource_id=request.request_id,
                    risk_level=request.risk_level,
                    approval_present=bool(request.metadata.get("approval_present")),
                    delegation_id=_metadata_str(request.metadata, "delegation_id"),
                    context={
                        "security_scope": request.scope,
                        "allow_external": request.allow_external,
                        "uses_external_model": provider.provider_id != DETERMINISTIC_PROVIDER_ID,
                        "provider_id": provider.provider_id,
                    },
                    metadata=request.metadata,
                )
            ),
        )

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, object],
    ) -> None:
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{node_id}-{event_type}",
                    trace_id=node_id,
                    event_type=cast(VisualTelemetryEventType, event_type),
                    node_type=cast(VisualNodeType, node_type),
                    node_id=node_id,
                    edge_from=None,
                    edge_to=None,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return

    def _observe(self, request: ModelGatewayRequest, response: ModelGatewayResponse) -> None:
        record_event = getattr(self._observability_service, "record_event", None)
        if not callable(record_event):
            return
        try:
            record_event(
                ObservabilityEvent(
                    observability_event_id=f"observability-{uuid4().hex}",
                    trace_id=request.trace_id,
                    correlation_id=None,
                    event_type="model_gateway_completed",
                    component="model_gateway",
                    level=_observability_level(response),
                    message="Model gateway request completed.",
                    payload={
                        "request_id": request.request_id,
                        "status": response.status,
                        "provider_id": response.usage.provider_id,
                    },
                    created_at=None,
                )
            )
        except Exception:
            return


def _policy_context(
    provider: ModelProvider,
    profile: ModelProfile,
    request: ModelGatewayRequest,
) -> dict[str, object]:
    return {
        "selected_provider": provider.provider_id,
        "provider_type": provider.provider_type,
        "selected_model": profile.model_name,
        "model_profile_id": profile.model_profile_id,
        "privacy_level": profile.privacy_level,
        "allow_external": request.allow_external,
    }


def _observability_level(response: ModelGatewayResponse) -> ObservabilityLevel:
    return "info" if response.status in {"completed", "fallback_used"} else "warning"


def _actor_context(request: ModelGatewayRequest) -> ActorContext:
    roles = (
        [str(item) for item in request.metadata.get("roles", [])]
        if isinstance(request.metadata.get("roles"), list)
        else []
    )
    permissions = (
        [str(item) for item in request.metadata.get("permissions", [])]
        if isinstance(request.metadata.get("permissions"), list)
        else []
    )
    return ActorContext(
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        roles=roles,
        permissions=permissions,
        security_scope=request.scope,
        trace_id=request.trace_id,
        dev_mode=bool(request.metadata.get("dev_mode", False)),
    )


def _metadata_str(metadata: dict[str, object], key: str) -> str | None:
    value = metadata.get(key)
    return value if isinstance(value, str) and value else None


def _safe_route(request: ModelGatewayRequest) -> ModelRouteDecision:
    return ModelRouteDecision(
        route_id=f"route-{request.request_id}",
        trace_id=request.trace_id,
        reasoning_id=request.reasoning_id,
        selected_provider=DETERMINISTIC_PROVIDER_ID,
        selected_model=DETERMINISTIC_MODEL_NAME,
        mode=request.mode,
        reason="safe_deterministic_route",
        fallback_providers=[],
        privacy_level="local",
        risk_level=request.risk_level,
        estimated_cost=0.0,
        estimated_latency_ms=0,
        created_at=datetime.now(UTC),
    )


def _blocked_call(
    request: ModelGatewayRequest,
    route: ModelRouteDecision,
    reason: str,
) -> ModelCallRecord:
    return ModelCallRecord(
        model_call_id=f"model-call-{request.request_id}",
        trace_id=request.trace_id,
        reasoning_id=request.reasoning_id,
        provider=route.selected_provider,
        model=route.selected_model,
        mode=request.mode,
        request={"request_id": request.request_id, "blocked": True},
        response={"reason": reason},
        status="blocked",
        latency_ms=0,
        cost_estimate=0.0,
        created_at=datetime.now(UTC),
    )


def _failed_call(route: ModelRouteDecision, reason: str) -> ModelCallRecord:
    return ModelCallRecord(
        model_call_id=f"model-call-{uuid4().hex}",
        trace_id=route.trace_id,
        reasoning_id=route.reasoning_id,
        provider=route.selected_provider,
        model=route.selected_model,
        mode=route.mode,
        request={"route_id": route.route_id},
        response={"reason": reason},
        status="failed",
        latency_ms=None,
        cost_estimate=0.0,
        created_at=datetime.now(UTC),
    )
