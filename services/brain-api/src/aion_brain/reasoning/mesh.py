"""AION Reasoning Mesh service."""

from datetime import UTC, datetime
from typing import Any, Protocol

from aion_brain.contracts.model_gateway import ModelGatewayRequest, ModelGatewayResponse
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reasoning import (
    ModelCallRecord,
    ModelRouteDecision,
    PromptPacket,
    ReasoningRequest,
    ReasoningResult,
)
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.reasoning.base import ModelGatewayAdapter
from aion_brain.reasoning.deterministic_adapter import DeterministicReasoningAdapter
from aion_brain.reasoning.prompt_builder import PromptBuilder
from aion_brain.reasoning.router import ModelRouter


class ReasoningRepositoryProtocol(Protocol):
    """Persistence boundary for reasoning artifacts."""

    def save_reasoning(
        self,
        result: ReasoningResult,
        *,
        status: str = "completed",
    ) -> ReasoningResult:
        """Persist a reasoning result."""
        ...

    def save_model_call(self, record: ModelCallRecord) -> ModelCallRecord:
        """Persist a model call record."""
        ...


class ModelGatewayCompletionProtocol(Protocol):
    """Provider-neutral gateway completion service boundary."""

    def complete(self, request: ModelGatewayRequest) -> ModelGatewayResponse:
        """Complete a model gateway request."""
        ...


class ReasoningMesh:
    """Policy-gated reasoning orchestration boundary."""

    def __init__(
        self,
        *,
        model_router: ModelRouter | None = None,
        prompt_builder: PromptBuilder | None = None,
        model_gateway_adapter: ModelGatewayAdapter | None = None,
        model_gateway_service: ModelGatewayCompletionProtocol | None = None,
        policy_adapter: PolicyAdapter,
        reasoning_repository: ReasoningRepositoryProtocol | object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._model_router = model_router or ModelRouter()
        self._prompt_builder = prompt_builder or PromptBuilder()
        self._model_gateway_adapter = model_gateway_adapter or DeterministicReasoningAdapter()
        self._model_gateway_service = model_gateway_service
        self._policy_adapter = policy_adapter
        self._reasoning_repository = reasoning_repository
        self._telemetry_service = telemetry_service

    def reason(self, request: ReasoningRequest) -> ReasoningResult:
        """Run a policy-gated reasoning pass."""
        self._emit_started(request)
        prompt = self._prompt_builder.build(request)
        route = self._model_router.route(request)

        reasoning_decision = self._authorize(
            request=request,
            action_type="reasoning.run",
            resource_type="reasoning",
            resource_id=request.reasoning_id,
            context={"mode": request.mode},
        )
        if not reasoning_decision.allow:
            return self._blocked_result(
                request=request,
                prompt=prompt,
                route=route,
                reason="reasoning_blocked_by_policy",
                decision=reasoning_decision,
            )

        if self._model_gateway_service is not None:
            gateway_response = self._complete_with_gateway(request, prompt)
            self._persist_model_call(gateway_response.model_call)
            result = _result_from_gateway_response(request, prompt, gateway_response)
            self._persist_reasoning(
                result,
                status=(
                    "completed"
                    if gateway_response.status in {"completed", "fallback_used"}
                    else gateway_response.status
                ),
            )
            self._emit_completed(result)
            return result

        route_decision = self._authorize(
            request=request,
            action_type="model.route",
            resource_type="model_route",
            resource_id=route.route_id,
            context={
                "selected_provider": route.selected_provider,
                "selected_model": route.selected_model,
                "mode": route.mode,
            },
        )
        if not route_decision.allow:
            return self._blocked_result(
                request=request,
                prompt=prompt,
                route=route,
                reason="model_route_blocked_by_policy",
                decision=route_decision,
            )
        self._emit_model_route(request, route)

        complete_decision = self._authorize(
            request=request,
            action_type="model.complete",
            resource_type="model_call",
            resource_id=None,
            context={
                "selected_provider": route.selected_provider,
                "selected_model": route.selected_model,
                "mode": route.mode,
            },
        )
        if not complete_decision.allow:
            return self._blocked_result(
                request=request,
                prompt=prompt,
                route=route,
                reason="model_complete_blocked_by_policy",
                decision=complete_decision,
            )

        model_call = self._model_gateway_adapter.complete(prompt, route)
        self._persist_model_call(model_call)
        self._emit_model_call(request, model_call)
        result = _result_from_model_call(request, prompt, route, model_call)
        self._persist_reasoning(result, status="completed")
        self._emit_completed(result)
        return result

    def _complete_with_gateway(
        self,
        request: ReasoningRequest,
        prompt: PromptPacket,
    ) -> ModelGatewayResponse:
        if self._model_gateway_service is None:
            raise RuntimeError("model gateway service is not configured")
        response = self._model_gateway_service.complete(
            ModelGatewayRequest(
                request_id=f"model-gateway-{request.reasoning_id}",
                trace_id=request.trace_id,
                reasoning_id=request.reasoning_id,
                prompt=prompt,
                mode=request.mode,
                risk_level=request.risk_level,
                actor_id=_optional_metadata_str(request, "actor_id"),
                workspace_id=_optional_metadata_str(request, "workspace_id"),
                scope=_security_scope(request),
                preferred_profile_id=_optional_metadata_str(request, "preferred_profile_id"),
                allow_external=bool(request.metadata.get("allow_external", False)),
                metadata=dict(request.metadata),
            )
        )
        if not isinstance(response, ModelGatewayResponse):
            raise TypeError("model gateway service returned a non-AION response")
        return response

    def _blocked_result(
        self,
        *,
        request: ReasoningRequest,
        prompt: PromptPacket,
        route: ModelRouteDecision,
        reason: str,
        decision: PolicyDecision,
    ) -> ReasoningResult:
        constraints = [reason, *decision.constraints]
        result = ReasoningResult(
            reasoning_id=request.reasoning_id,
            trace_id=request.trace_id,
            context_id=request.context.context_id,
            mode=request.mode,
            summary="Reasoning did not run because policy denied the request.",
            interpretation="Policy denied the reasoning boundary before model completion.",
            suggested_next_actions=["ask_clarifying_question"],
            constraints=constraints,
            confidence=0.0,
            requires_clarification=True,
            clarification_questions=[
                "Policy authorization is required before reasoning can continue."
            ],
            route_decision=route,
            prompt_packet=prompt,
            metadata={
                "status": "blocked_by_policy",
                "policy_decision_id": decision.decision_id,
                "policy_reason": decision.reason,
            },
            created_at=datetime.now(UTC),
        )
        self._persist_reasoning(result, status="blocked_by_policy")
        self._emit_completed(result)
        return result

    def _authorize(
        self,
        *,
        request: ReasoningRequest,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or request.reasoning_id}",
                trace_id=request.trace_id,
                actor_id=_optional_metadata_str(request, "actor_id"),
                workspace_id=_optional_metadata_str(request, "workspace_id"),
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=request.risk_level,
                approval_present=False,
                requested_permissions=[],
                security_scope=_security_scope(request),
                context=context,
            )
        )

    def _persist_reasoning(self, result: ReasoningResult, *, status: str) -> None:
        save = getattr(self._reasoning_repository, "save_reasoning", None)
        if not callable(save):
            return
        try:
            save(result, status=status)
        except Exception:
            return

    def _persist_model_call(self, record: ModelCallRecord) -> None:
        save = getattr(self._reasoning_repository, "save_model_call", None)
        if not callable(save):
            return
        try:
            save(record)
        except Exception:
            return

    def _emit_started(self, request: ReasoningRequest) -> None:
        self._emit(
            request.trace_id or request.reasoning_id,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{request.reasoning_id}-reasoning-started",
                trace_id=request.trace_id or request.reasoning_id,
                event_type="reasoning_started",
                node_type="reasoning",
                node_id=request.reasoning_id,
                edge_from=request.context.context_id,
                edge_to=request.reasoning_id,
                intensity=0.4,
                payload={"mode": request.mode},
                created_at=datetime.now(UTC),
            ),
        )

    def _emit_model_route(self, request: ReasoningRequest, route: ModelRouteDecision) -> None:
        self._emit(
            request.trace_id or request.reasoning_id,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{request.reasoning_id}-model-route-selected",
                trace_id=request.trace_id or request.reasoning_id,
                event_type="model_route_selected",
                node_type="model",
                node_id=route.selected_model,
                edge_from=request.reasoning_id,
                edge_to=route.selected_model,
                intensity=0.5,
                payload={"provider": route.selected_provider, "reason": route.reason},
                created_at=datetime.now(UTC),
            ),
        )

    def _emit_model_call(self, request: ReasoningRequest, record: ModelCallRecord) -> None:
        self._emit(
            request.trace_id or request.reasoning_id,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{request.reasoning_id}-model-call-recorded",
                trace_id=request.trace_id or request.reasoning_id,
                event_type="model_call_recorded",
                node_type="model",
                node_id=record.model_call_id,
                edge_from=record.model,
                edge_to=record.model_call_id,
                intensity=0.6,
                payload={"status": record.status, "provider": record.provider},
                created_at=datetime.now(UTC),
            ),
        )

    def _emit_completed(self, result: ReasoningResult) -> None:
        self._emit(
            result.trace_id or result.reasoning_id,
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{result.reasoning_id}-reasoning-completed",
                trace_id=result.trace_id or result.reasoning_id,
                event_type="reasoning_completed",
                node_type="reasoning",
                node_id=result.reasoning_id,
                edge_from=result.route_decision.selected_model,
                edge_to=result.reasoning_id,
                intensity=result.confidence,
                payload={
                    "requires_clarification": result.requires_clarification,
                    "status": result.metadata.get("status", "completed"),
                },
                created_at=datetime.now(UTC),
            ),
        )

    def _emit(self, trace_id: str, event: VisualTelemetryEvent) -> None:
        if self._telemetry_service is None:
            return
        try:
            save = getattr(self._telemetry_service, "save_visual_telemetry", None)
            if callable(save):
                save(trace_id, [event])
                return
            emit = getattr(self._telemetry_service, "emit", None)
            if callable(emit):
                emit(event)
        except Exception:
            return


def _result_from_model_call(
    request: ReasoningRequest,
    prompt: PromptPacket,
    route: ModelRouteDecision,
    model_call: ModelCallRecord,
) -> ReasoningResult:
    response = model_call.response
    return ReasoningResult(
        reasoning_id=request.reasoning_id,
        trace_id=request.trace_id,
        context_id=request.context.context_id,
        mode=request.mode,
        summary=str(response.get("summary", "")),
        interpretation=str(response.get("interpretation", "")),
        suggested_next_actions=_string_list(response.get("suggested_next_actions")),
        constraints=list(request.context.constraints),
        confidence=_bounded_float(response.get("confidence")),
        requires_clarification=bool(response.get("requires_clarification", False)),
        clarification_questions=_string_list(response.get("clarification_questions")),
        route_decision=route,
        prompt_packet=prompt,
        metadata={
            "status": model_call.status,
            "model_call_id": model_call.model_call_id,
        },
        created_at=datetime.now(UTC),
    )


def _result_from_gateway_response(
    request: ReasoningRequest,
    prompt: PromptPacket,
    gateway_response: ModelGatewayResponse,
) -> ReasoningResult:
    result = _result_from_model_call(
        request,
        prompt,
        gateway_response.route_decision,
        gateway_response.model_call,
    )
    constraints = list(result.constraints)
    if gateway_response.reason is not None and gateway_response.status != "completed":
        constraints.append(gateway_response.reason)
    return result.model_copy(
        update={
            "route_decision": gateway_response.route_decision,
            "constraints": constraints,
            "metadata": {
                **result.metadata,
                "status": gateway_response.status,
                "model_call_id": gateway_response.model_call.model_call_id,
                "usage_id": gateway_response.usage.usage_id,
                "model_usage": gateway_response.usage.model_dump(mode="json"),
                "redaction": (
                    gateway_response.redaction.model_dump(mode="json")
                    if gateway_response.redaction is not None
                    else None
                ),
            },
        }
    )


def _optional_metadata_str(request: ReasoningRequest, key: str) -> str | None:
    value = request.metadata.get(key)
    if value is None:
        return None
    return str(value)


def _security_scope(request: ReasoningRequest) -> list[str]:
    value = request.metadata.get("security_scope")
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return value
    return ["workspace:main"]


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _bounded_float(value: object) -> float:
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    return 0.0
