"""Brain loop goal and task lifecycle metadata tests."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.goals import GoalCreateRequest, GoalRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.policy import PolicyDecision
from aion_brain.contracts.state import BrainState
from aion_brain.contracts.tasks import CognitiveTask, TaskCreateRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.core.brain_loop import BrainLoopService
from aion_brain.evaluation.evaluator import Evaluator
from aion_brain.learning.engine import LearningEngine
from aion_brain.telemetry.visual import VisualTelemetryBuilder


class FakeRuntime:
    """Runtime fake that returns a public BrainState."""

    def run_state(self, event: AIONEvent) -> BrainState:
        return BrainState(
            event=event,
            trace=DecisionTrace(
                trace_id=event.trace_id or "trace-1",
                event_id=event.event_id,
                intent_id="intent-1",
                context_id="context-1",
                plan_id="plan-1",
                memory_refs=[],
                capability_refs=[],
                policy_decisions=[],
                outcome={
                    "status": "planned",
                    "runtime": "langgraph",
                    "message": "AION Brain completed deterministic planning loop.",
                },
                created_at=datetime.now(UTC),
            ),
            policy_decisions=[],
            status="planned",
        )


class FakeAuditLedger:
    """Audit ledger fake that records persisted artifacts."""

    def __init__(self) -> None:
        self.traces: list[DecisionTrace] = []
        self.telemetry: list[VisualTelemetryEvent] = []

    def record(self, trace: DecisionTrace) -> DecisionTrace:
        self.traces.append(trace)
        return trace

    def record_policy_decisions(
        self,
        trace_id: str,
        decisions: list[PolicyDecision],
    ) -> None:
        return None

    def record_evaluation(self, evaluation: EvaluationRecord) -> EvaluationRecord:
        return evaluation

    def record_learning_signal(self, signal: LearningSignal) -> LearningSignal:
        return signal

    def record_visual_telemetry(
        self,
        trace_id: str,
        events: list[VisualTelemetryEvent],
    ) -> None:
        self.telemetry.extend(events)


class FakeGoalService:
    """Goal service fake for Brain loop tests."""

    def __init__(self) -> None:
        self.requests: list[GoalCreateRequest] = []

    def create_goal(self, request: GoalCreateRequest) -> GoalRecord:
        self.requests.append(request)
        return GoalRecord(
            goal_id=request.goal_id or "goal-created",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            title=request.title,
            description=request.description,
            status="proposed",
            priority=request.priority,
            risk_level=request.risk_level,
            owner_scope=request.owner_scope,
            constraints=request.constraints,
            success_criteria=request.success_criteria,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


class FakeTaskService:
    """Task service fake for Brain loop tests."""

    def __init__(self) -> None:
        self.requests: list[TaskCreateRequest] = []

    def create_task(self, request: TaskCreateRequest) -> CognitiveTask:
        self.requests.append(request)
        return CognitiveTask(
            task_id=request.task_id or "task-created",
            goal_id=request.goal_id,
            trace_id=request.trace_id,
            plan_id=request.plan_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            title=request.title,
            description=request.description,
            task_type=request.task_type,
            status="proposed",
            priority=request.priority,
            risk_level=request.risk_level,
            owner_scope=request.owner_scope,
            input=request.input,
            constraints=request.constraints,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )


def test_brain_loop_advertises_lifecycle_endpoints_without_creating_records() -> None:
    """Brain think advertises goal/task endpoints without implicit creation."""
    goal_service = FakeGoalService()
    task_service = FakeTaskService()
    audit = FakeAuditLedger()
    service = make_service(audit, goal_service, task_service)

    trace = service.think(make_event(payload={"question": "what next?"}))

    assert trace.outcome["can_create_goal"] is True
    assert trace.outcome["can_create_task"] is True
    assert trace.outcome["goal_endpoint"] == "/brain/goals"
    assert trace.outcome["task_endpoint"] == "/brain/tasks"
    assert "goal_id" not in trace.outcome
    assert "task_id" not in trace.outcome
    assert goal_service.requests == []
    assert task_service.requests == []
    assert audit.traces[0].outcome == trace.outcome


def test_brain_loop_creates_goal_and_task_only_when_payload_flags_are_true() -> None:
    """Explicit payload flags create proposed lifecycle records."""
    goal_service = FakeGoalService()
    task_service = FakeTaskService()
    audit = FakeAuditLedger()
    service = make_service(audit, goal_service, task_service)

    trace = service.think(
        make_event(
            payload={
                "create_goal": True,
                "create_task": True,
                "goal": "Keep a generic objective",
                "description": "Track it as a proposed lifecycle record.",
                "priority": "high",
                "risk_level": "medium",
                "task_type": "brain.plan",
            }
        )
    )

    assert trace.outcome["goal_id"] == "goal-created"
    assert trace.outcome["task_id"] == "task-created"
    assert goal_service.requests[0].title == "Keep a generic objective"
    assert task_service.requests[0].goal_id == "goal-created"
    assert task_service.requests[0].plan_id == "plan-1"
    assert task_service.requests[0].task_type == "brain.plan"
    assert {event.event_type for event in audit.telemetry} >= {"goal_created", "task_created"}


def test_replay_mode_disables_goal_and_task_side_effects() -> None:
    """Explicit replay mode suppresses lifecycle creation inside the Brain loop."""
    goal_service = FakeGoalService()
    task_service = FakeTaskService()
    audit = FakeAuditLedger()
    service = make_service(audit, goal_service, task_service)

    trace = service.think(
        make_event(payload={"create_goal": True, "create_task": True}),
        replay_mode=True,
    )

    assert trace.outcome["replay"] is True
    assert trace.outcome["side_effects"] == "disabled"
    assert goal_service.requests == []
    assert task_service.requests == []


def make_service(
    audit: FakeAuditLedger,
    goal_service: FakeGoalService,
    task_service: FakeTaskService,
) -> BrainLoopService:
    """Create a Brain loop service with deterministic fakes."""
    return BrainLoopService(
        runtime=FakeRuntime(),  # type: ignore[arg-type]
        audit_ledger=audit,  # type: ignore[arg-type]
        evaluator=Evaluator(),
        learning_engine=LearningEngine(),
        telemetry_builder=VisualTelemetryBuilder(),
        goal_service=goal_service,  # type: ignore[arg-type]
        task_service=task_service,  # type: ignore[arg-type]
    )


def make_event(payload: dict[str, object]) -> AIONEvent:
    """Create a normalized event."""
    return AIONEvent(
        event_id="event-1",
        source="test",
        event_type="question.answer",
        actor_id="actor-1",
        workspace_id="workspace-1",
        payload_type="test.payload",
        payload=payload,
        timestamp=datetime.now(UTC),
        correlation_id="corr-1",
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )
