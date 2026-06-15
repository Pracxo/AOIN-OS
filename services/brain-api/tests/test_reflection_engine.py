"""Reflection engine tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.reflection import ReflectionRecord, ReflectionRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.reflection.engine import ReflectionEngine


class FakePolicyAdapter:
    """Policy fake for reflection tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeReflectionRepository:
    """In-memory reflection repository fake."""

    def __init__(self) -> None:
        self.reflections: dict[str, ReflectionRecord] = {}

    def save_reflection(self, reflection: ReflectionRecord) -> ReflectionRecord:
        self.reflections[reflection.reflection_id] = reflection
        return reflection


class FakeTelemetry:
    """Telemetry fake for reflection tests."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_reflection_engine_calls_policy_before_creating_reflection() -> None:
    """Reflection creation is policy-gated."""
    policy = FakePolicyAdapter()
    repository = FakeReflectionRepository()
    telemetry = FakeTelemetry()
    reflection = ReflectionEngine(
        reflection_repository=repository,
        learning_engine=None,
        policy_adapter=policy,
        telemetry_service=telemetry,
    ).reflect(ReflectionRequest(trace=make_trace(), evaluation=make_evaluation()))

    assert policy.requests[0].action_type == "reflection.create"
    assert reflection.reflection_id in repository.reflections
    assert telemetry.events[0].event_type == "reflection_created"


def test_reflection_policy_deny_blocks_reflection() -> None:
    """Policy denial prevents reflection persistence."""
    repository = FakeReflectionRepository()

    with pytest.raises(ValueError, match="policy_denied"):
        ReflectionEngine(
            reflection_repository=repository,
            learning_engine=None,
            policy_adapter=FakePolicyAdapter(allow=False),
        ).reflect(ReflectionRequest(trace=make_trace(), evaluation=make_evaluation()))

    assert repository.reflections == {}


def test_reflection_engine_creates_generic_low_score_observation() -> None:
    """Low deterministic evaluation scores create generic observations."""
    reflection = make_engine().reflect(
        ReflectionRequest(trace=make_trace(), evaluation=make_evaluation(plan_score=0.4))
    )

    assert "low_score:plan_quality_score" in reflection.observations
    assert any(
        change["change_type"] == "generic_procedure"
        for change in reflection.proposed_changes
    )


def test_reflection_engine_creates_policy_observation() -> None:
    """Blocked traces create a policy observation."""
    trace = make_trace(status="blocked_by_policy")

    reflection = make_engine().reflect(ReflectionRequest(trace=trace, evaluation=make_evaluation()))

    assert "policy_constraint_observed" in reflection.observations


def make_engine() -> ReflectionEngine:
    """Create a reflection engine with fakes."""
    return ReflectionEngine(
        reflection_repository=FakeReflectionRepository(),
        learning_engine=None,
        policy_adapter=FakePolicyAdapter(),
    )


def make_trace(status: str = "planned") -> DecisionTrace:
    """Create a decision trace."""
    return DecisionTrace(
        trace_id="trace-1",
        event_id="event-1",
        intent_id="intent-1",
        context_id="context-1",
        plan_id="plan-1",
        memory_refs=[],
        capability_refs=[],
        policy_decisions=[],
        outcome={"status": status},
        created_at=datetime.now(UTC),
    )


def make_evaluation(plan_score: float = 0.8) -> EvaluationRecord:
    """Create an evaluation record."""
    return EvaluationRecord(
        evaluation_id="evaluation-1",
        trace_id="trace-1",
        scores={"plan_quality_score": plan_score, "memory_relevance_score": 0.4},
        lessons=[],
        created_at=datetime.now(UTC),
    )
