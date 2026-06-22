"""Deterministic Reflection Engine."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reflection import ReflectionRecord, ReflectionRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.reflection.repository import ReflectionRepository


class ReflectionEngine:
    """Creates controlled procedural learning reflections without model calls."""

    def __init__(
        self,
        *,
        reflection_repository: ReflectionRepository | object,
        learning_engine: object | None,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = reflection_repository
        self._learning_engine = learning_engine
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def reflect(self, request: ReflectionRequest) -> ReflectionRecord:
        """Create and persist a deterministic reflection record."""
        decision = self._authorize(request)
        if not decision.allow:
            raise ValueError(f"policy_denied:{decision.reason}")

        observations = _observations(request)
        proposed_changes = _proposed_changes(request)
        risks = _risks(request, proposed_changes)
        confidence = _confidence(request, observations, risks)
        reflection = ReflectionRecord(
            reflection_id=request.reflection_id or f"reflection-{uuid4().hex}",
            trace_id=request.trace.trace_id if request.trace else None,
            task_id=request.task.task_id if request.task else None,
            task_run_id=request.task_run.task_run_id if request.task_run else None,
            execution_id=request.execution.execution_id if request.execution else None,
            evaluation_id=request.evaluation.evaluation_id if request.evaluation else None,
            learning_signal_ids=[signal.learning_id for signal in request.learning_signals],
            reflection_type=request.reflection_type,
            observations=observations or ["generic reflection recorded"],
            proposed_changes=proposed_changes,
            risks=risks,
            confidence=confidence,
            status="recorded",
            created_at=datetime.now(UTC),
        )
        saved = _save_reflection(self._repository, reflection)
        self._emit(saved)
        return saved

    def _authorize(self, request: ReflectionRequest) -> PolicyDecision:
        trace = request.trace
        risk_level = "medium" if request.reflection_type.endswith("_review") else "low"
        return self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"reflection.create-{request.reflection_id or uuid4().hex}",
                trace_id=trace.trace_id if trace else None,
                actor_id=request.event.actor_id if request.event else None,
                workspace_id=request.event.workspace_id if request.event else None,
                action_type="reflection.create",
                resource_type="reflection",
                resource_id=request.reflection_id,
                risk_level=risk_level,
                approval_present=False,
                requested_permissions=[],
                security_scope=(
                    request.event.security_scope if request.event else ["workspace:main"]
                ),
                context={"reflection_type": request.reflection_type},
            )
        )

    def _emit(self, reflection: ReflectionRecord) -> None:
        event = VisualTelemetryEvent(
            telemetry_id=f"telemetry-{reflection.reflection_id}-created",
            trace_id=reflection.trace_id or reflection.reflection_id,
            event_type="reflection_created",
            node_type="reflection",
            node_id=reflection.reflection_id,
            edge_from=reflection.trace_id,
            edge_to=reflection.reflection_id,
            intensity=reflection.confidence,
            payload={"reflection_type": reflection.reflection_type, "status": reflection.status},
            created_at=datetime.now(UTC),
        )
        _emit(self._telemetry_service, event)


def _observations(request: ReflectionRequest) -> list[str]:
    observations: list[str] = []
    if request.evaluation is not None:
        for score_name, score in request.evaluation.scores.items():
            if score < 0.5:
                observations.append(f"low_score:{score_name}")
        if request.evaluation.scores.get("memory_relevance_score", 1.0) < 0.5:
            observations.append("retrieval_improvement_opportunity")
    if request.trace is not None and request.trace.outcome.get("status") == "blocked_by_policy":
        observations.append("policy_constraint_observed")
    if request.trace is not None and request.trace.outcome.get("status") in {
        "planned",
        "completed",
    }:
        observations.append("successful_plan_pattern_observed")
    if request.task_run is not None and request.task_run.status == "completed":
        observations.append("completed_task_pattern_observed")
    if request.execution is not None and request.execution.status == "completed":
        observations.append("completed_execution_pattern_observed")
    if request.trace is not None and request.trace.outcome.get("reasoning_requires_clarification"):
        observations.append("clarification_needed_observed")
    return _unique(observations)


def _proposed_changes(request: ReflectionRequest) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    if _successful_pattern(request):
        changes.append(
            {
                "change_type": "generic_procedure",
                "name": "Generic planning procedure",
                "description": "Reuse a reviewed generic Brain procedure as procedural memory.",
                "trigger_patterns": _trigger_patterns(request),
                "procedure_steps": [
                    "retrieve_context",
                    "compile_context",
                    "reason",
                    "create_plan",
                    "policy_check",
                    "evaluate_result",
                    "record_learning",
                ],
                "expected_outcomes": ["reviewed_generic_procedure_available"],
            }
        )
    if (
        request.evaluation is not None
        and request.evaluation.scores.get("memory_relevance_score", 1.0) < 0.5
    ):
        changes.append(
            {
                "change_type": "retrieval_tuning",
                "description": "Improve future context retrieval with generic procedural memory.",
            }
        )
    if request.trace is not None and request.trace.outcome.get("reasoning_requires_clarification"):
        changes.append(
            {
                "change_type": "generic_procedure",
                "name": "Generic clarification procedure",
                "description": "Ask for missing context before planning continues.",
                "trigger_patterns": ["unknown", "clarification.ask"],
                "procedure_steps": ["ask_clarifying_question", "record_learning"],
                "expected_outcomes": ["missing_context_requested"],
            }
        )
    return changes


def _risks(request: ReflectionRequest, proposed_changes: list[dict[str, Any]]) -> list[str]:
    risks: list[str] = []
    if any(change.get("risk_level") in {"high", "critical"} for change in proposed_changes):
        risks.append("high_risk_procedure_requires_approval")
    if not request.learning_signals and request.evaluation is None:
        risks.append("insufficient_evidence")
    source_count = 1 if request.trace is not None else 0
    source_count += 1 if request.task is not None else 0
    if source_count <= 1:
        risks.append("narrow_source_trace")
    return _unique(risks)


def _confidence(
    request: ReflectionRequest,
    observations: list[str],
    risks: list[str],
) -> float:
    score = 0.55
    if request.evaluation is not None and request.evaluation.scores:
        score = sum(request.evaluation.scores.values()) / len(request.evaluation.scores)
    if request.task_run is not None and request.task_run.status == "completed":
        score = max(score, 0.72)
    if request.execution is not None and request.execution.status == "completed":
        score = max(score, 0.74)
    if observations:
        score += 0.05
    if "insufficient_evidence" in risks:
        score -= 0.2
    if "narrow_source_trace" in risks:
        score -= 0.05
    return max(0.0, min(1.0, round(score, 4)))


def _successful_pattern(request: ReflectionRequest) -> bool:
    if request.task_run is not None and request.task_run.status == "completed":
        return True
    if request.execution is not None and request.execution.status == "completed":
        return True
    if request.trace is not None and request.trace.outcome.get("status") in {
        "planned",
        "completed",
    }:
        return True
    return False


def _trigger_patterns(request: ReflectionRequest) -> list[str]:
    patterns: list[str] = []
    if request.trace is not None:
        if request.trace.intent_id:
            patterns.append(request.trace.intent_id)
        status = request.trace.outcome.get("status")
        if isinstance(status, str):
            patterns.append(status)
    if request.task is not None:
        patterns.append(request.task.task_type)
    if request.execution is not None:
        patterns.extend(step.action_type for step in request.execution.steps)
    if not patterns:
        patterns.append(request.reflection_type)
    return _unique(patterns)


def _save_reflection(repository: object, reflection: ReflectionRecord) -> ReflectionRecord:
    save = getattr(repository, "save_reflection", None)
    if callable(save):
        result = save(reflection)
        if isinstance(result, ReflectionRecord):
            return result
    return reflection


def _emit(telemetry_service: object | None, event: VisualTelemetryEvent) -> None:
    if telemetry_service is None:
        return
    emit = getattr(telemetry_service, "emit", None)
    if callable(emit):
        emit(event)
        return
    save = getattr(telemetry_service, "save_visual_telemetry", None)
    if callable(save):
        save(event.trace_id, [event])


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
