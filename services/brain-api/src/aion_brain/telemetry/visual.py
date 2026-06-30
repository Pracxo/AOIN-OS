"""Visual Brain telemetry event generation."""

from datetime import UTC, datetime
from typing import cast

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.contracts.traces import DecisionTrace

CONNECTOR_RUNTIME_TELEMETRY_EVENTS = (
    "connector_runtime_status_checked",
    "connector_manifest_validated",
    "connector_egress_preview_created",
    "connector_ingress_preview_created",
    "connector_runtime_audit_completed",
)

CONNECTOR_SIMULATOR_TELEMETRY_EVENTS = (
    "connector_simulation_completed",
    "connector_policy_readiness_checked",
)

CONNECTOR_POLICY_TELEMETRY_EVENTS = (
    "connector_policy_catalog_read",
    "connector_authorization_matrix_read",
    "connector_policy_dry_run_completed",
    "connector_policy_traceability_queried",
)


class VisualTelemetryBuilder:
    """Build visual telemetry events for future Brain graph animation."""

    def build(
        self,
        *,
        trace: DecisionTrace,
        policy_decisions: list[PolicyDecision],
        evaluation: EvaluationRecord,
        learning_signal: LearningSignal,
    ) -> list[VisualTelemetryEvent]:
        """Create deterministic visual telemetry for a completed loop."""
        events = [
            _event(
                trace,
                "brain_loop_started",
                "event",
                trace.event_id,
                None,
                trace.intent_id,
                0.5,
            ),
        ]
        if trace.intent_id:
            events.append(
                _event(
                    trace,
                    "intent_classified",
                    "intent",
                    trace.intent_id,
                    trace.event_id,
                    trace.intent_id,
                    0.7,
                )
            )
        if trace.context_id:
            events.append(
                _event(
                    trace,
                    "context_compiled",
                    "context",
                    trace.context_id,
                    trace.intent_id,
                    trace.context_id,
                    0.7,
                )
            )
        for reasoning_id in trace.reasoning_refs:
            model_id = _outcome_str(trace, "reasoning_model") or "deterministic-reasoner-v0"
            model_call_id = _outcome_str(trace, "model_call_id")
            events.extend(
                [
                    _event(
                        trace,
                        "reasoning_started",
                        "reasoning",
                        reasoning_id,
                        trace.context_id,
                        reasoning_id,
                        0.4,
                    ),
                    _event(
                        trace,
                        "model_route_selected",
                        "model",
                        model_id,
                        reasoning_id,
                        model_id,
                        0.5,
                        {"provider": trace.outcome.get("reasoning")},
                    ),
                ]
            )
            if model_call_id:
                events.append(
                    _event(
                        trace,
                        "model_call_recorded",
                        "model",
                        model_call_id,
                        model_id,
                        model_call_id,
                        0.6,
                    )
                )
            events.append(
                _event(
                    trace,
                    "reasoning_completed",
                    "reasoning",
                    reasoning_id,
                    model_call_id or model_id,
                    reasoning_id,
                    _reasoning_intensity(trace),
                    {
                        "requires_clarification": trace.outcome.get(
                            "reasoning_requires_clarification"
                        )
                    },
                )
            )
        for memory_id in trace.memory_refs:
            events.append(
                _event(
                    trace,
                    "memory_node_activated",
                    "memory",
                    memory_id,
                    trace.context_id,
                    memory_id,
                    0.8,
                )
            )
        for capability_id in trace.capability_refs:
            events.append(
                _event(
                    trace,
                    "capability_node_seen",
                    "capability",
                    capability_id,
                    trace.context_id,
                    capability_id,
                    0.6,
                )
            )
        goal_id = _outcome_str(trace, "goal_id")
        if goal_id:
            events.append(
                _event(
                    trace,
                    "goal_created",
                    "goal",
                    goal_id,
                    trace.trace_id,
                    goal_id,
                    0.5,
                )
            )
        task_id = _outcome_str(trace, "task_id")
        if task_id:
            events.append(
                _event(
                    trace,
                    "task_created",
                    "task",
                    task_id,
                    goal_id or trace.trace_id,
                    task_id,
                    0.5,
                )
            )
        reflection_id = _outcome_str(trace, "reflection_id")
        if reflection_id:
            events.append(
                _event(
                    trace,
                    "reflection_created",
                    "reflection",
                    reflection_id,
                    trace.trace_id,
                    reflection_id,
                    0.7,
                )
            )
        candidate_id = _outcome_str(trace, "candidate_id")
        if candidate_id:
            events.append(
                _event(
                    trace,
                    "skill_candidate_created",
                    "candidate",
                    candidate_id,
                    reflection_id or trace.trace_id,
                    candidate_id,
                    0.7,
                )
            )
        if trace.plan_id:
            events.append(
                _event(
                    trace,
                    "plan_step_created",
                    "plan",
                    trace.plan_id,
                    trace.context_id,
                    trace.plan_id,
                    0.75,
                )
            )
        for execution_id in trace.execution_refs:
            events.append(
                _event(
                    trace,
                    "execution_started",
                    "execution",
                    execution_id,
                    trace.plan_id,
                    execution_id,
                    0.4,
                )
            )
            events.append(
                _event(
                    trace,
                    "execution_completed",
                    "execution",
                    execution_id,
                    execution_id,
                    trace.trace_id,
                    1.0,
                    {"execution_status": trace.outcome.get("execution_status")},
                )
            )
        for decision in policy_decisions:
            event_type = "policy_checked" if decision.allow else "policy_blocked"
            events.append(
                _event(
                    trace,
                    event_type,
                    "policy",
                    decision.decision_id,
                    trace.plan_id,
                    decision.decision_id,
                    0.95 if not decision.allow else 0.7,
                    {"reason": decision.reason, "allow": decision.allow},
                )
            )
        events.extend(
            [
                _event(
                    trace,
                    "trace_created",
                    "trace",
                    trace.trace_id,
                    trace.plan_id,
                    trace.trace_id,
                    0.9,
                ),
                _event(
                    trace,
                    "evaluation_completed",
                    "evaluation",
                    evaluation.evaluation_id,
                    trace.trace_id,
                    evaluation.evaluation_id,
                    0.8,
                ),
                _event(
                    trace,
                    "learning_signal_created",
                    "learning",
                    learning_signal.learning_id,
                    evaluation.evaluation_id,
                    learning_signal.learning_id,
                    0.7,
                ),
                _event(
                    trace,
                    "brain_loop_completed",
                    "trace",
                    trace.trace_id,
                    learning_signal.learning_id,
                    trace.trace_id,
                    1.0,
                    {"outcome_status": trace.outcome.get("status")},
                ),
            ]
        )
        return events


def _outcome_str(trace: DecisionTrace, key: str) -> str | None:
    value = trace.outcome.get(key)
    if isinstance(value, str):
        return value
    return None


def _reasoning_intensity(trace: DecisionTrace) -> float:
    value = trace.outcome.get("reasoning_confidence")
    if isinstance(value, int | float):
        return max(0.0, min(1.0, float(value)))
    return 0.0


def build_graph_memory_activation_event(
    *,
    object_id: str,
    intensity: float,
    edge_from: str | None = None,
    edge_to: str | None = None,
    payload: dict[str, object] | None = None,
) -> VisualTelemetryEvent:
    """Create visual telemetry for graph memory activation."""
    return VisualTelemetryEvent(
        telemetry_id=f"telemetry-graph-memory-{object_id}",
        trace_id=f"graph-memory-{object_id}",
        event_type="memory_node_activated",
        node_type="memory",
        node_id=object_id,
        edge_from=edge_from,
        edge_to=edge_to,
        intensity=intensity,
        payload=payload or {},
        created_at=datetime.now(UTC),
    )


def build_operator_console_telemetry_event(
    *,
    telemetry_id: str,
    event_type: str,
    node_type: str,
    node_id: str,
    scope: list[str],
    payload: dict[str, object] | None = None,
) -> VisualTelemetryEvent:
    """Create visual telemetry for read-only Operator Console projections."""
    return VisualTelemetryEvent(
        telemetry_id=telemetry_id,
        trace_id=telemetry_id,
        event_type=cast(VisualTelemetryEventType, event_type),
        node_type=cast(VisualNodeType, node_type),
        node_id=node_id,
        edge_from=None,
        edge_to=None,
        intensity=0.5,
        payload={
            "owner_scope": scope,
            "read_only": True,
            "frontend_enabled": False,
            "production_auth": False,
            **(payload or {}),
        },
        created_at=datetime.now(UTC),
    )


def _event(
    trace: DecisionTrace,
    event_type: str,
    node_type: str,
    node_id: str,
    edge_from: str | None,
    edge_to: str | None,
    intensity: float,
    payload: dict[str, object] | None = None,
) -> VisualTelemetryEvent:
    projection_context: dict[str, object] = {}
    workspace_id = trace.outcome.get("workspace_id")
    if isinstance(workspace_id, str):
        projection_context["workspace_id"] = workspace_id
    owner_scope = trace.outcome.get("security_scope")
    if isinstance(owner_scope, list):
        projection_context["owner_scope"] = [str(item) for item in owner_scope]
    return VisualTelemetryEvent(
        telemetry_id=f"telemetry-{trace.trace_id}-{event_type}-{node_id}",
        trace_id=trace.trace_id,
        event_type=cast(VisualTelemetryEventType, event_type),
        node_type=cast(VisualNodeType, node_type),
        node_id=node_id,
        edge_from=edge_from,
        edge_to=edge_to,
        intensity=intensity,
        payload={**projection_context, **(payload or {})},
        created_at=datetime.now(UTC),
    )
