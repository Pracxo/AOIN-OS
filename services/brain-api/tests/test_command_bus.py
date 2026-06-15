"""Command Bus tests."""

from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.commands.bus import CommandBus
from aion_brain.commands.handlers import CommandHandlerRegistry
from aion_brain.commands.repository import CommandRepository
from aion_brain.config import Settings
from aion_brain.contracts.commands import CommandDispatchRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.idempotency.repository import IdempotencyRepository
from aion_brain.idempotency.service import IdempotencyService
from aion_brain.outbox.repository import OutboxRepository
from aion_brain.outbox.service import OutboxService


class FakePolicy:
    """Policy fake."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="policy-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeAutonomy:
    """Autonomy fake."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[object] = []

    def decide(self, request: object) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(
            autonomy_decision_id="autonomy-1",
            allow=self.allow,
            reason="allowed" if self.allow else "autonomy_denied",
            constraints=[],
        )


class FakeRisk:
    """Risk fake."""

    def __init__(self, decision: str = "allow") -> None:
        self.decision = decision

    def assess(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(risk_assessment_id="risk-1", decision=self.decision)


class FakeApproval:
    """Approval fake."""

    def __init__(self) -> None:
        self.requests: list[object] = []

    def create_request(self, request: object) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(approval_request_id="approval-1")


def test_command_bus_dispatches_noop_dry_run() -> None:
    """Command Bus dispatches noop in dry-run mode."""
    bus, policy, autonomy, _approval = make_bus()

    result = bus.dispatch(request())

    assert result.command.status == "completed"
    assert result.duplicate is False
    assert result.outbox_ids
    assert policy.requests[0].action_type == "command.dispatch"
    assert autonomy.requests


def test_command_bus_blocks_duplicate_command_through_idempotency() -> None:
    """Completed idempotent commands suppress duplicate execution."""
    bus, _policy, _autonomy, _approval = make_bus()
    first = bus.dispatch(request(idempotency_key="idem-command"))

    second = bus.dispatch(request(idempotency_key="idem-command"))

    assert first.command.status == "completed"
    assert second.duplicate is True
    assert second.command.command_id == first.command.command_id


def test_command_bus_calls_policy_before_dispatch() -> None:
    """Policy is called for command.dispatch."""
    bus, policy, _autonomy, _approval = make_bus()

    bus.dispatch(request())

    assert policy.requests


def test_policy_deny_blocks_command() -> None:
    """Policy denial blocks the command."""
    bus, _policy, _autonomy, _approval = make_bus(policy=FakePolicy(allow=False))

    result = bus.dispatch(request())

    assert result.command.status == "blocked_by_policy"


def test_command_bus_calls_autonomy_governor() -> None:
    """Autonomy Governor is invoked."""
    bus, _policy, autonomy, _approval = make_bus()

    bus.dispatch(request())

    assert autonomy.requests


def test_autonomy_deny_blocks_command() -> None:
    """Autonomy denial blocks the command."""
    bus, _policy, _autonomy, _approval = make_bus(autonomy=FakeAutonomy(allow=False))

    result = bus.dispatch(request())

    assert result.command.status == "blocked_by_autonomy"


def test_command_bus_creates_approval_when_required() -> None:
    """Risk approval requirement creates an approval request."""
    approval = FakeApproval()
    bus, _policy, _autonomy, _approval = make_bus(
        risk=FakeRisk(decision="require_approval"),
        approval=approval,
    )

    result = bus.dispatch(request(mode="controlled"))

    assert result.command.status == "waiting_for_approval"
    assert approval.requests


def make_bus(
    *,
    policy: FakePolicy | None = None,
    autonomy: FakeAutonomy | None = None,
    risk: FakeRisk | None = None,
    approval: FakeApproval | None = None,
) -> tuple[CommandBus, FakePolicy, FakeAutonomy, FakeApproval]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    settings = Settings(
        _env_file=None,
        DATABASE_URL="sqlite+pysqlite:///:memory:",
        AION_DEFAULT_SEMANTIC_ADAPTER="in_memory",
        AION_GRAPH_MEMORY_ADAPTER="in_memory",
        AION_OUTBOX_PROCESS_ENABLED=True,
    )
    selected_policy = policy or FakePolicy()
    selected_autonomy = autonomy or FakeAutonomy()
    selected_approval = approval or FakeApproval()
    outbox = OutboxService(OutboxRepository(engine=engine), settings=settings)
    bus = CommandBus(
        command_repository=CommandRepository(engine=engine),
        command_handlers=CommandHandlerRegistry(),
        idempotency_service=IdempotencyService(
            IdempotencyRepository(engine=engine),
            settings=settings,
        ),
        policy_adapter=selected_policy,
        autonomy_governor=selected_autonomy,
        risk_engine=risk or FakeRisk(),
        approval_service=selected_approval,
        outbox_service=outbox,
        telemetry_service=None,
        settings=settings,
    )
    return bus, selected_policy, selected_autonomy, selected_approval


def request(idempotency_key: str | None = None, mode: str = "dry_run") -> CommandDispatchRequest:
    return CommandDispatchRequest(
        command_type="noop",
        target_type="noop",
        mode=mode,  # type: ignore[arg-type]
        idempotency_key=idempotency_key,
        owner_scope=["workspace:main"],
    )
