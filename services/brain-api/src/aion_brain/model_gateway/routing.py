"""Deterministic planning-only routing, fallback, retry, cost, and latency."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.model_gateway import (
    DETERMINISTIC_PROVIDER_ID,
    MAXIMUM_FALLBACK_CANDIDATES_PER_REQUEST,
    MAXIMUM_RETRY_ATTEMPTS_PLANNED_PER_REQUEST,
    REFERENCE_JSON_MODEL_ID,
    REFERENCE_TEXT_MODEL_ID,
    ModelCapabilityProfile,
    ModelCircuitBreakerState,
    ModelFallbackPlan,
    ModelGatewayCostEstimate,
    ModelGatewayLatencyEstimate,
    ModelGatewayOutputMode,
    ModelGatewayRequestEnvelope,
    ModelGatewayRouteDisposition,
    ModelManifest,
    ModelProviderManifest,
    ModelRetryPlan,
    ModelRoutingCandidate,
    ModelRoutingPlan,
    ensure_gateway_utc,
)


def estimate_cost(
    *, estimated_input_tokens: int, estimated_output_tokens: int
) -> ModelGatewayCostEstimate:
    """Return a deterministic estimate; no live provider charge exists."""

    return ModelGatewayCostEstimate(
        estimated_cost_microunits=estimated_input_tokens + estimated_output_tokens
    )


def estimate_latency(
    *, estimated_input_tokens: int, estimated_output_tokens: int
) -> ModelGatewayLatencyEstimate:
    """Return deterministic latency estimate independent of provider telemetry."""

    return ModelGatewayLatencyEstimate(
        estimated_latency_milliseconds=25
        + ((estimated_input_tokens + estimated_output_tokens) // 100)
    )


def plan_route(
    *,
    routing_plan_id: str,
    request: ModelGatewayRequestEnvelope,
    provider_manifest: ModelProviderManifest,
    model_manifests: tuple[ModelManifest, ...],
    capability_profiles: tuple[ModelCapabilityProfile, ...],
    circuit_states: tuple[ModelCircuitBreakerState, ...],
    estimated_input_tokens: int,
    estimated_output_tokens: int,
    created_at: datetime,
) -> ModelRoutingPlan:
    """Plan a deterministic route without executing it."""

    profile_by_model = {profile.model_id: profile for profile in capability_profiles}
    circuit_by_model = {state.model_id: state for state in circuit_states}
    candidates = []
    for model in sorted(model_manifests, key=lambda item: item.model_id):
        profile = profile_by_model[model.model_id]
        circuit = circuit_by_model[model.model_id]
        output_match = request.requested_output_mode in model.output_modes
        token_fit = (
            estimated_input_tokens <= model.maximum_input_tokens
            and estimated_output_tokens <= model.maximum_output_tokens
        )
        context_fit = token_fit
        structured_fit = (
            request.requested_output_mode != ModelGatewayOutputMode.structured_json
            or model.model_id == REFERENCE_JSON_MODEL_ID
        )
        candidates.append(
            ModelRoutingCandidate(
                provider_id=provider_manifest.provider_id,
                model_id=model.model_id,
                provider_manifest_fingerprint=provider_manifest.manifest_fingerprint or "",
                model_manifest_fingerprint=model.manifest_fingerprint or "",
                capability_profile_fingerprint=profile.profile_fingerprint or "",
                operation=request.operation,
                context_fit=context_fit,
                token_fit=token_fit,
                output_mode_fit=output_match,
                structured_schema_fit=structured_fit,
                circuit_breaker_status=circuit.status,
                estimated_input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimated_output_tokens,
                estimated_cost_microunits=estimate_cost(
                    estimated_input_tokens=estimated_input_tokens,
                    estimated_output_tokens=estimated_output_tokens,
                ).estimated_cost_microunits,
                estimated_latency_milliseconds=estimate_latency(
                    estimated_input_tokens=estimated_input_tokens,
                    estimated_output_tokens=estimated_output_tokens,
                ).estimated_latency_milliseconds,
            )
        )
    ranked = sorted(candidates, key=_candidate_rank)
    selected = next((item for item in ranked if _candidate_eligible(item)), None)
    return ModelRoutingPlan(
        routing_plan_id=routing_plan_id,
        request_fingerprint=request.request_fingerprint or "",
        candidates=tuple(ranked),
        selected_provider_id=selected.provider_id if selected else None,
        selected_model_id=selected.model_id if selected else None,
        disposition=(
            ModelGatewayRouteDisposition.selected
            if selected
            else ModelGatewayRouteDisposition.blocked
        ),
        reason_codes=("route_selected",) if selected else ("route_blocked",),
        created_at=ensure_gateway_utc(created_at),
    )


def plan_fallback(
    *,
    fallback_plan_id: str,
    request: ModelGatewayRequestEnvelope,
    routing_plan: ModelRoutingPlan,
    created_at: datetime,
) -> ModelFallbackPlan:
    """Plan deterministic fallback candidates without executing them."""

    primary = routing_plan.selected_model_id or REFERENCE_TEXT_MODEL_ID
    fallback_ids = tuple(
        item.model_id
        for item in routing_plan.candidates
        if item.model_id != primary and _candidate_eligible(item)
    )[:MAXIMUM_FALLBACK_CANDIDATES_PER_REQUEST]
    return ModelFallbackPlan(
        fallback_plan_id=fallback_plan_id,
        request_fingerprint=request.request_fingerprint or "",
        primary_model_id=primary,
        fallback_model_ids=fallback_ids,
        created_at=ensure_gateway_utc(created_at),
    )


def plan_retry(
    *,
    retry_plan_id: str,
    request: ModelGatewayRequestEnvelope,
    planned_attempts: int = MAXIMUM_RETRY_ATTEMPTS_PLANNED_PER_REQUEST,
    created_at: datetime,
) -> ModelRetryPlan:
    """Plan deterministic retries without executing them."""

    delays = tuple(50 * (index + 1) for index in range(planned_attempts))
    return ModelRetryPlan(
        retry_plan_id=retry_plan_id,
        request_fingerprint=request.request_fingerprint or "",
        planned_attempts=planned_attempts,
        deterministic_delay_milliseconds=delays,
        created_at=ensure_gateway_utc(created_at),
    )


def _candidate_eligible(candidate: ModelRoutingCandidate) -> bool:
    return (
        candidate.context_fit
        and candidate.token_fit
        and candidate.output_mode_fit
        and candidate.structured_schema_fit
        and candidate.circuit_breaker_status.value != "open"
    )


def _candidate_rank(candidate: ModelRoutingCandidate) -> tuple[object, ...]:
    operation_fit = candidate.operation in {
        "text_generate_simulate",
        "structured_generate_simulate",
    }
    preferred = 0
    if candidate.model_id == REFERENCE_TEXT_MODEL_ID:
        preferred = 1
    if candidate.operation.value == "structured_generate_simulate":
        preferred = 0 if candidate.model_id == REFERENCE_JSON_MODEL_ID else 1
    return (
        not operation_fit,
        not candidate.context_fit,
        not candidate.token_fit,
        not candidate.structured_schema_fit,
        not _candidate_eligible(candidate),
        candidate.estimated_cost_microunits,
        candidate.estimated_latency_milliseconds,
        DETERMINISTIC_PROVIDER_ID != candidate.provider_id,
        preferred,
        candidate.provider_id,
        candidate.model_id,
    )
