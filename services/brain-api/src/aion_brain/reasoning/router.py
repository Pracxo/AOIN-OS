"""Deterministic model router for AION v0.1."""

from datetime import UTC, datetime

from aion_brain.contracts.reasoning import ModelRouteDecision, ReasoningRequest

LOCAL_PROVIDER = "deterministic"
LOCAL_MODEL = "deterministic-reasoner-v0"


class ModelRouter:
    """Select the local deterministic model boundary for v0.1."""

    def route(self, request: ReasoningRequest) -> ModelRouteDecision:
        """Return a deterministic local route decision."""
        return ModelRouteDecision(
            route_id=f"route-{request.reasoning_id}",
            trace_id=request.trace_id,
            reasoning_id=request.reasoning_id,
            selected_provider=LOCAL_PROVIDER,
            selected_model=LOCAL_MODEL,
            mode=request.mode,
            reason="v0.1 uses deterministic local reasoning by default",
            fallback_providers=[],
            privacy_level="local",
            risk_level=request.risk_level,
            estimated_cost=0.0,
            estimated_latency_ms=0,
            created_at=datetime.now(UTC),
        )
