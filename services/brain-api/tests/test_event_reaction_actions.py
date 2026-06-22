"""Event reaction action runner tests."""

from datetime import UTC, datetime

from aion_brain.contracts.cycles import CognitiveCycleRunRequest
from aion_brain.contracts.event_reactions import EventReactionAction, EventSubscription
from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.modules import CapabilityInvocationRequest
from aion_brain.contracts.workflows import WorkflowRunRequest
from aion_brain.event_reactions.actions import EventReactionActionRunner


class FakeAttentionController:
    """Attention fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_signal(self, request: object) -> dict[str, object]:
        self.requests.append(request)
        return {"created": True}


class FakeTaskService:
    """Task fake."""

    def __init__(self) -> None:
        self.created: list[object] = []
        self.runs: list[object] = []

    def create_task(self, request: object) -> dict[str, object]:
        self.created.append(request)
        return {"task_id": "task-1"}


class FakeWorkflowService:
    """Workflow fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def run_workflow(self, request: WorkflowRunRequest) -> dict[str, object]:
        self.requests.append(request)
        return {"workflow_run_id": "workflow-run-1", "mode": request.mode}


class FakeCycleOrchestrator:
    """Cycle fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def run_cycle(self, request: CognitiveCycleRunRequest) -> dict[str, object]:
        self.requests.append(request)
        return {"cycle_run_id": "cycle-run-1", "mode": request.mode}


class FakeCapabilityGateway:
    """Capability gateway fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def invoke(self, request: CapabilityInvocationRequest) -> dict[str, object]:
        self.requests.append(request)
        return {
            "invocation_id": request.invocation_id,
            "mode": request.mode,
        }


def test_action_runner_creates_attention_signal() -> None:
    """Attention signal target creates a generic attention signal."""
    attention = FakeAttentionController()
    runner = EventReactionActionRunner(attention_controller=attention)

    result = runner.run(
        action=action("attention_signal"),
        event=event(),
        subscription=subscription("attention_signal"),
    )

    assert result.status == "completed"
    assert len(attention.requests) == 1


def test_action_runner_creates_task_without_running_it() -> None:
    """Task target creates a task but never runs it."""
    task_service = FakeTaskService()
    runner = EventReactionActionRunner(task_service=task_service)

    result = runner.run(
        action=action("task"),
        event=event(),
        subscription=subscription("task"),
    )

    assert result.status == "completed"
    assert len(task_service.created) == 1
    assert task_service.runs == []
    assert result.output["ran"] is False


def test_action_runner_keeps_workflow_cycle_and_capability_in_dry_run_by_default() -> None:
    """Controlled action requests downgrade sensitive targets to dry-run unless opted in."""
    workflow = FakeWorkflowService()
    cycle = FakeCycleOrchestrator()
    capability = FakeCapabilityGateway()
    runner = EventReactionActionRunner(
        workflow_service=workflow,
        cognitive_cycle_orchestrator=cycle,
        capability_runtime_gateway=capability,
    )

    workflow_result = runner.run(
        action=action("workflow", mode="controlled"),
        event=event(),
        subscription=subscription("workflow", target_id="workflow-1"),
    )
    cycle_result = runner.run(
        action=action("cognitive_cycle", mode="controlled"),
        event=event(),
        subscription=subscription("cognitive_cycle"),
    )
    capability_result = runner.run(
        action=action("capability", mode="controlled"),
        event=event(),
        subscription=subscription("capability", target_id="test.echo"),
    )

    assert workflow_result.output["mode"] == "dry_run"
    assert cycle_result.output["mode"] == "dry_run"
    assert capability_result.output["mode"] == "dry_run"


def test_action_runner_dry_run_has_no_side_effect() -> None:
    """Runner dry-run returns a planned action without calling target services."""
    attention = FakeAttentionController()
    runner = EventReactionActionRunner(attention_controller=attention)

    result = runner.dry_run(
        action=action("attention_signal"),
        event=event(),
        subscription=subscription("attention_signal"),
    )

    assert result.status == "dry_run"
    assert result.output["dry_run"] is True
    assert attention.requests == []


def event() -> AIONEvent:
    """Create a normalized event."""
    return AIONEvent(
        event_id="event-1",
        source="test-suite",
        event_type="generic.received",
        payload_type="generic.payload",
        payload={"message": "hello"},
        timestamp=datetime.now(UTC),
        trace_id="trace-1",
        security_scope=["workspace:main"],
    )


def subscription(
    target_type: str,
    *,
    target_id: str | None = None,
) -> EventSubscription:
    """Create a subscription."""
    return EventSubscription(
        subscription_id="sub-1",
        name="Generic subscription",
        description="React to generic events.",
        owner_scope=["workspace:main"],
        event_type_patterns=["generic.*"],
        target_type=target_type,  # type: ignore[arg-type]
        target_id=target_id,
        reaction_mode="controlled",
    )


def action(target_type: str, *, mode: str = "controlled") -> EventReactionAction:
    """Create a reaction action."""
    return EventReactionAction(
        reaction_action_id=f"action-{target_type}",
        dispatch_id="dispatch-1",
        subscription_id="sub-1",
        event_id="event-1",
        trace_id="trace-1",
        target_type=target_type,  # type: ignore[arg-type]
        action_type=f"{target_type}.run",
        mode=mode,  # type: ignore[arg-type]
        status="running",
        input={"approval_present": False},
    )
