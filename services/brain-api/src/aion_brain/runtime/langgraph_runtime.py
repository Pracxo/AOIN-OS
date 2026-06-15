"""LangGraph runtime adapter boundary."""

from datetime import UTC, datetime
from typing import Any, TypedDict, cast

from langgraph.graph import END, START, StateGraph

from aion_brain.context.compiler import ContextCompiler
from aion_brain.contracts.context import ContextPacket
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.intent import IntentFrame
from aion_brain.contracts.planning import PlanGraph
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reasoning import (
    ReasoningRequest,
    ReasoningResult,
    ReasoningRiskLevel,
)
from aion_brain.contracts.state import BrainState
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.intent.engine import IntentEngine
from aion_brain.planning.planner import Planner
from aion_brain.policy.base import PolicyAdapter
from aion_brain.reasoning.mesh import ReasoningMesh


class _RuntimeState(TypedDict, total=False):
    event: AIONEvent
    scope: list[str]
    intent: IntentFrame | None
    context: ContextPacket | None
    reasoning: ReasoningResult | None
    plan: PlanGraph | None
    policy_decisions: list[PolicyDecision]
    trace: DecisionTrace | None
    errors: list[str]
    status: str
    execution_ready: bool
    execution_approval_required: bool


class LangGraphRuntimeAdapter:
    """Adapter boundary for LangGraph.

    LangGraph-specific imports and graph objects remain private to this module.
    Public callers receive only AION-owned contracts.
    """

    def __init__(
        self,
        *,
        intent_engine: IntentEngine,
        context_compiler: ContextCompiler,
        planner: Planner,
        policy_adapter: PolicyAdapter,
        reasoning_mesh: ReasoningMesh | None = None,
        default_scope: list[str] | None = None,
    ) -> None:
        self._intent_engine = intent_engine
        self._context_compiler = context_compiler
        self._planner = planner
        self._policy_adapter = policy_adapter
        self._reasoning_mesh = reasoning_mesh or ReasoningMesh(policy_adapter=policy_adapter)
        self._default_scope = default_scope or ["workspace:main"]
        self._graph: Any = self._build_graph()

    def run(self, event: AIONEvent) -> DecisionTrace:
        """Run the deterministic Brain loop and return a decision trace."""
        state = self.run_state(event)
        if state.trace is not None:
            return state.trace
        return _fallback_trace(event, state.errors or ["runtime_returned_no_trace"])

    def run_state(self, event: AIONEvent) -> BrainState:
        """Run the deterministic Brain loop and return the public Brain state."""
        initial_state: _RuntimeState = {
            "event": event,
            "scope": event.security_scope or self._default_scope,
            "intent": None,
            "context": None,
            "reasoning": None,
            "plan": None,
            "policy_decisions": [],
            "trace": None,
            "errors": [],
            "status": "started",
            "execution_ready": False,
            "execution_approval_required": False,
        }
        result = self._graph.invoke(initial_state)
        if isinstance(result, dict):
            return _state_from_result(event, result)
        return BrainState(
            event=event,
            trace=_fallback_trace(event, ["runtime_returned_no_state"]),
            errors=["runtime_returned_no_state"],
            status="error",
        )

    def _build_graph(self) -> Any:
        graph = StateGraph(_RuntimeState)
        graph.add_node("classify_intent", self._classify_intent)
        graph.add_node("compile_context", self._compile_context)
        graph.add_node("run_reasoning", self._run_reasoning)
        graph.add_node("create_plan", self._create_plan)
        graph.add_node("authorize_plan", self._authorize_plan)
        graph.add_node("create_trace", self._create_trace)
        graph.add_edge(START, "classify_intent")
        graph.add_edge("classify_intent", "compile_context")
        graph.add_edge("compile_context", "run_reasoning")
        graph.add_edge("run_reasoning", "create_plan")
        graph.add_edge("create_plan", "authorize_plan")
        graph.add_edge("authorize_plan", "create_trace")
        graph.add_edge("create_trace", END)
        return graph.compile()

    def _classify_intent(self, state: _RuntimeState) -> _RuntimeState:
        event = state["event"]
        return {"intent": self._intent_engine.from_event(event), "status": "intent_classified"}

    def _compile_context(self, state: _RuntimeState) -> _RuntimeState:
        event = state["event"]
        intent = state.get("intent")
        if intent is None:
            return _append_error(state, "intent_missing_before_context")
        context = self._context_compiler.compile(
            event=event,
            intent=intent,
            scope=state.get("scope", self._default_scope),
        )
        return {"context": context, "status": "context_compiled"}

    def _run_reasoning(self, state: _RuntimeState) -> _RuntimeState:
        event = state["event"]
        intent = state.get("intent")
        context = state.get("context")
        if context is None:
            return _append_error(state, "context_missing_before_reasoning")
        reasoning = self._reasoning_mesh.reason(
            ReasoningRequest(
                reasoning_id=f"reasoning-{event.event_id}",
                trace_id=event.trace_id,
                intent=intent,
                context=context,
                mode="plan_assist",
                risk_level=_risk_level(intent.risk_level if intent else "low"),
                metadata={
                    "actor_id": event.actor_id,
                    "workspace_id": event.workspace_id,
                    "security_scope": event.security_scope,
                },
            )
        )
        if reasoning.metadata.get("status") == "blocked_by_policy":
            return {"reasoning": reasoning, "status": "blocked_by_policy"}
        return {"reasoning": reasoning, "status": "reasoning_completed"}

    def _create_plan(self, state: _RuntimeState) -> _RuntimeState:
        if state.get("status") == "blocked_by_policy":
            return {"status": "blocked_by_policy"}
        context = state.get("context")
        if context is None:
            return _append_error(state, "context_missing_before_plan")
        return {
            "plan": self._planner.create_plan(context, state.get("reasoning")),
            "status": "plan_created",
        }

    def _authorize_plan(self, state: _RuntimeState) -> _RuntimeState:
        if state.get("status") == "blocked_by_policy":
            return {"status": "blocked_by_policy"}
        event = state["event"]
        plan = state.get("plan")
        if plan is None:
            return _append_error(state, "plan_missing_before_policy")

        decisions = list(state.get("policy_decisions", []))
        plan_decision = self._authorize(
            event=event,
            action_type="plan.create",
            resource_type="plan",
            resource_id=plan.plan_id,
            risk_level=plan.risk_level,
            context={"intent_id": plan.intent_id},
        )
        decisions.append(plan_decision)
        if not plan_decision.allow:
            return {"policy_decisions": decisions, "status": "blocked_by_policy"}

        for step in plan.steps:
            decision = self._authorize(
                event=event,
                action_type=step.action_type,
                resource_type="plan_step",
                resource_id=step.step_id,
                risk_level=step.risk_level,
                context={"plan_id": plan.plan_id, "step_id": step.step_id},
            )
            decisions.append(decision)
            if not decision.allow:
                return {"policy_decisions": decisions, "status": "blocked_by_policy"}

        execution_decision = self._authorize(
            event=event,
            action_type="plan.execute",
            resource_type="plan",
            resource_id=plan.plan_id,
            risk_level=plan.risk_level,
            context={"plan_id": plan.plan_id, "mode": "dry_run"},
        )
        decisions.append(execution_decision)

        return {
            "policy_decisions": decisions,
            "status": "planned",
            "execution_ready": execution_decision.allow,
            "execution_approval_required": execution_decision.approval_required,
        }

    def _create_trace(self, state: _RuntimeState) -> _RuntimeState:
        event = state["event"]
        intent = state.get("intent")
        context = state.get("context")
        reasoning = state.get("reasoning")
        plan = state.get("plan")
        decisions = state.get("policy_decisions", [])
        status = state.get("status", "planned")
        trace = DecisionTrace(
            trace_id=event.trace_id or f"trace-{event.event_id}",
            event_id=event.event_id,
            intent_id=intent.intent_id if intent else None,
            context_id=context.context_id if context else None,
            plan_id=plan.plan_id if plan else None,
            memory_refs=context.retrieved_memory_ids if context else [],
            capability_refs=context.available_capability_ids if context else [],
            reasoning_refs=[reasoning.reasoning_id] if reasoning else [],
            execution_refs=[],
            policy_decisions=[decision.decision_id for decision in decisions],
            outcome=_outcome(
                status,
                state.get("errors", []),
                reasoning,
                execution_ready=bool(state.get("execution_ready", False)),
                execution_approval_required=bool(
                    state.get("execution_approval_required", False)
                ),
            ),
            created_at=datetime.now(UTC),
        )
        return {"trace": trace, "status": status}

    def _authorize(
        self,
        *,
        event: AIONEvent,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        risk_level: str,
        context: dict[str, Any],
    ) -> PolicyDecision:
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or event.event_id}",
                trace_id=event.trace_id,
                actor_id=event.actor_id,
                workspace_id=event.workspace_id,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[],
                security_scope=event.security_scope,
                context=context,
            )
        )


def _append_error(state: _RuntimeState, error: str) -> _RuntimeState:
    errors = list(state.get("errors", []))
    errors.append(error)
    return {"errors": errors, "status": "error"}


def _outcome(
    status: str,
    errors: list[str],
    reasoning: ReasoningResult | None = None,
    *,
    execution_ready: bool = False,
    execution_approval_required: bool = False,
) -> dict[str, Any]:
    reasoning_payload = _reasoning_outcome(reasoning)
    execution_payload = {
        "execution_ready": execution_ready,
        "execution_approval_required": execution_approval_required,
        "execution_endpoint": "/brain/execute",
    }
    if status == "blocked_by_policy":
        return {
            "status": "blocked_by_policy",
            "runtime": "langgraph",
            **reasoning_payload,
            **execution_payload,
            "message": (
                "AION Brain deterministic reasoning and planning loop was blocked by policy."
            ),
            "errors": errors,
        }
    return {
        "status": "planned",
        "runtime": "langgraph",
        **reasoning_payload,
        **execution_payload,
        "message": "AION Brain completed deterministic reasoning and planning loop.",
        "errors": errors,
    }


def _reasoning_outcome(reasoning: ReasoningResult | None) -> dict[str, Any]:
    if reasoning is None:
        return {}
    payload: dict[str, Any] = {
        "reasoning": "deterministic-local",
        "reasoning_id": reasoning.reasoning_id,
        "reasoning_model": reasoning.route_decision.selected_model,
        "reasoning_confidence": reasoning.confidence,
        "reasoning_requires_clarification": reasoning.requires_clarification,
    }
    model_call_id = reasoning.metadata.get("model_call_id")
    if isinstance(model_call_id, str):
        payload["model_call_id"] = model_call_id
    return payload


def _fallback_trace(event: AIONEvent, errors: list[str]) -> DecisionTrace:
    return DecisionTrace(
        trace_id=event.trace_id or f"trace-{event.event_id}",
        event_id=event.event_id,
        intent_id=None,
        context_id=None,
        plan_id=None,
        memory_refs=[],
        capability_refs=[],
        reasoning_refs=[],
        execution_refs=[],
        policy_decisions=[],
        outcome=_outcome("blocked_by_policy", errors),
        created_at=datetime.now(UTC),
    )


def _state_from_result(event: AIONEvent, result: dict[str, Any]) -> BrainState:
    intent = result.get("intent")
    context = result.get("context")
    reasoning = result.get("reasoning")
    plan = result.get("plan")
    decisions = result.get("policy_decisions", [])
    trace = result.get("trace")
    errors = result.get("errors", [])
    status = result.get("status", "completed")

    return BrainState(
        event=event,
        intent=intent if isinstance(intent, IntentFrame) else None,
        context=context if isinstance(context, ContextPacket) else None,
        reasoning=reasoning if isinstance(reasoning, ReasoningResult) else None,
        plan=plan if isinstance(plan, PlanGraph) else None,
        policy_decisions=[
            decision for decision in decisions if isinstance(decision, PolicyDecision)
        ]
        if isinstance(decisions, list)
        else [],
        trace=trace if isinstance(trace, DecisionTrace) else None,
        errors=[str(error) for error in errors] if isinstance(errors, list) else [],
        status=str(status),
    )


def _risk_level(value: str) -> ReasoningRiskLevel:
    if value in {"low", "medium", "high", "critical"}:
        return cast(ReasoningRiskLevel, value)
    return "low"
