"""Cognitive cycle orchestrator tests."""

from types import SimpleNamespace

from aion_brain.config import Settings
from aion_brain.contracts.cycles import (
    CognitiveCycleRun,
    CognitiveCycleRunRequest,
    CognitiveCycleStep,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.cycles.orchestrator import CognitiveCycleOrchestrator
from aion_brain.cycles.repository import CognitiveCycleRepository
from aion_brain.cycles.sleep import SleepConsolidationService


class FakePolicyAdapter:
    """Policy fake."""

    def __init__(self, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[],
            audit_level="standard",
        )


class FakeMaintenanceService:
    """Maintenance fake."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def run_step(
        self,
        step: CognitiveCycleStep,
        cycle_run: CognitiveCycleRun,
        dry_run: bool,
    ) -> dict[str, object]:
        step_type = step.step_type
        self.calls.append((str(step_type), dry_run))
        return {"step_type": step_type, "dry_run": dry_run}


class FakeAutonomyGovernor:
    """Autonomy fake."""

    def decide(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(
            allow=True,
            approval_required=False,
            autonomy_decision_id="autonomy-1",
            reason="allowed",
        )


class FakeApprovalService:
    """Approval fake."""

    def create_request(self, request: object) -> SimpleNamespace:
        return SimpleNamespace(approval_request_id="approval-1")


def test_orchestrator_runs_dry_sleep_cycle_without_live_dependencies(tmp_path) -> None:
    """Dry-run sleep cycles complete and persist a consolidation record."""
    policy = FakePolicyAdapter()
    maintenance = FakeMaintenanceService()
    repository = CognitiveCycleRepository(f"sqlite:///{tmp_path / 'cycles.db'}")
    sleep_service = SleepConsolidationService(cycle_repository=repository)
    orchestrator = CognitiveCycleOrchestrator(
        cycle_repository=repository,
        autonomy_governor=None,
        risk_engine=None,
        approval_service=None,
        policy_adapter=policy,
        telemetry_service=None,
        sleep_consolidation_service=sleep_service,
        maintenance_service=maintenance,
        settings=Settings(),
    )

    run = orchestrator.run_cycle(
        CognitiveCycleRunRequest(
            cycle_type="sleep_consolidation",
            owner_scope=["workspace:main"],
        )
    )

    assert run.status == "completed"
    assert run.mode == "dry_run"
    assert run.output["sleep_consolidation_id"].startswith("sleep-consolidation-")
    assert all(call[1] is True for call in maintenance.calls)
    assert policy.requests[0].action_type == "cycle.run"


def test_orchestrator_policy_deny_blocks_cycle(tmp_path) -> None:
    """Policy denial blocks a cycle before steps run."""
    maintenance = FakeMaintenanceService()
    orchestrator = CognitiveCycleOrchestrator(
        cycle_repository=CognitiveCycleRepository(f"sqlite:///{tmp_path / 'cycles.db'}"),
        autonomy_governor=None,
        risk_engine=None,
        approval_service=None,
        policy_adapter=FakePolicyAdapter(allow=False),
        telemetry_service=None,
        sleep_consolidation_service=None,
        maintenance_service=maintenance,
        settings=Settings(),
    )

    run = orchestrator.run_cycle(
        CognitiveCycleRunRequest(cycle_type="review", owner_scope=["workspace:main"])
    )

    assert run.status == "blocked_by_policy"
    assert maintenance.calls == []


def test_orchestrator_controlled_mode_waits_for_approval(tmp_path) -> None:
    """Controlled mode requires approval before work runs."""
    maintenance = FakeMaintenanceService()
    orchestrator = CognitiveCycleOrchestrator(
        cycle_repository=CognitiveCycleRepository(f"sqlite:///{tmp_path / 'cycles.db'}"),
        autonomy_governor=FakeAutonomyGovernor(),
        risk_engine=None,
        approval_service=FakeApprovalService(),
        policy_adapter=FakePolicyAdapter(),
        telemetry_service=None,
        sleep_consolidation_service=None,
        maintenance_service=maintenance,
        settings=Settings(),
    )

    run = orchestrator.run_cycle(
        CognitiveCycleRunRequest(
            cycle_type="maintenance",
            mode="controlled",
            owner_scope=["workspace:main"],
        )
    )

    assert run.status == "waiting_for_approval"
    assert run.approval_request_id == "approval-1"
    assert maintenance.calls == []
