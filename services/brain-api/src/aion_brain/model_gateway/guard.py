"""Model-gateway guard evaluation."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    ZERO_FINGERPRINT,
    ModelCircuitBreakerState,
    ModelFallbackPlan,
    ModelGatewayAuthorizationEnvelope,
    ModelGatewayComponentInvocationBinding,
    ModelGatewayContextBudgetDecision,
    ModelGatewayCostEstimate,
    ModelGatewayGuardDecision,
    ModelGatewayGuardOutcome,
    ModelGatewayLatencyEstimate,
    ModelGatewayRequestEnvelope,
    ModelGatewaySession,
    ModelGatewayTokenBudgetDecision,
    ModelManifest,
    ModelProviderManifest,
    ModelRetryPlan,
    ModelRoutingPlan,
    ensure_gateway_utc,
)
from aion_brain.contracts.secure_runtime import (
    SecureCapabilityInvocationPlan,
    SecureRuntimeGuardDecision,
    SecureRuntimeGuardOutcome,
    SecureRuntimeKillSwitchState,
    SecureRuntimeKillSwitchStatus,
    SecureRuntimeSession,
)


class ModelGatewayGuardEvaluator:
    """Precedence-ordered guard evaluator for reference simulation only."""

    def evaluate(
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
        provider_manifest: ModelProviderManifest,
        model_manifest: ModelManifest,
        capability_profile_fingerprint: str,
        context_budget_decision: ModelGatewayContextBudgetDecision,
        token_budget_decision: ModelGatewayTokenBudgetDecision,
        routing_plan: ModelRoutingPlan,
        fallback_plan: ModelFallbackPlan,
        retry_plan: ModelRetryPlan,
        circuit_breaker_state: ModelCircuitBreakerState,
        cost_estimate: ModelGatewayCostEstimate,
        latency_estimate: ModelGatewayLatencyEstimate,
        created_at: datetime,
    ) -> ModelGatewayGuardDecision:
        """Return allow_reference_simulation only when every parent control passes."""

        reasons: list[str] = []
        if parent_kill_switch.status != SecureRuntimeKillSwitchStatus.clear:
            reasons.append("parent_kill_switch_active")
        if authorization.authorization_transaction_id != "AION-232-SRI-0002":
            reasons.append("authorization_mismatch")
        if component_binding.binding_fingerprint != (
            authorization.secure_runtime_component_binding.binding_fingerprint
        ):
            reasons.append("component_binding_mismatch")
        if parent_capability_plan.capability_code != "brain.think.simulate":
            reasons.append("parent_capability_mismatch")
        if parent_runtime_guard.outcome != SecureRuntimeGuardOutcome.allow_simulation:
            reasons.append("parent_runtime_guard_not_allow_simulation")
        if secure_runtime_session.expires_at <= ensure_gateway_utc(created_at):
            reasons.append("parent_session_expired")
        if gateway_session.status.value != "active":
            reasons.append("gateway_session_not_active")
        if not context_budget_decision.allowed:
            reasons.append("context_budget_blocked")
        if not token_budget_decision.allowed:
            reasons.append("token_budget_blocked")
        if routing_plan.disposition.value != "selected":
            reasons.append("route_not_selected")
        if circuit_breaker_state.status.value == "open":
            reasons.append("circuit_open")
        if model_manifest.model_id != routing_plan.selected_model_id:
            reasons.append("model_route_mismatch")
        if provider_manifest.provider_id != routing_plan.selected_provider_id:
            reasons.append("provider_route_mismatch")
        outcome = (
            ModelGatewayGuardOutcome.allow_reference_simulation
            if not reasons
            else ModelGatewayGuardOutcome.block
        )
        return ModelGatewayGuardDecision(
            decision_id=decision_id,
            outcome=outcome,
            reason_codes=tuple(reasons or ("guard_allowed",)),
            authorization_envelope_fingerprint=authorization.envelope_fingerprint or "",
            component_binding_fingerprint=component_binding.binding_fingerprint or "",
            secure_runtime_session_fingerprint=secure_runtime_session.session_fingerprint or "",
            parent_capability_plan_fingerprint=parent_capability_plan.plan_fingerprint or "",
            parent_runtime_guard_fingerprint=parent_runtime_guard.guard_decision_fingerprint or "",
            parent_kill_switch_fingerprint=parent_kill_switch.state_fingerprint or ZERO_FINGERPRINT,
            gateway_session_fingerprint=gateway_session.session_fingerprint or "",
            request_fingerprint=request.request_fingerprint or "",
            provider_manifest_fingerprint=provider_manifest.manifest_fingerprint or "",
            model_manifest_fingerprint=model_manifest.manifest_fingerprint or "",
            capability_profile_fingerprint=capability_profile_fingerprint,
            context_budget_decision_fingerprint=context_budget_decision.decision_fingerprint or "",
            token_budget_decision_fingerprint=token_budget_decision.decision_fingerprint or "",
            routing_plan_fingerprint=routing_plan.plan_fingerprint or "",
            fallback_plan_fingerprint=fallback_plan.plan_fingerprint or "",
            retry_plan_fingerprint=retry_plan.plan_fingerprint or "",
            circuit_breaker_state_fingerprint=circuit_breaker_state.state_fingerprint or "",
            cost_estimate_fingerprint=cost_estimate.estimate_fingerprint or "",
            latency_estimate_fingerprint=latency_estimate.estimate_fingerprint or "",
            created_at=ensure_gateway_utc(created_at),
        )
