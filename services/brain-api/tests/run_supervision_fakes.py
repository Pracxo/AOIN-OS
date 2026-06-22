"""Shared fakes for run supervision tests."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.config import Settings
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.run_supervision import RunSupervisionCreateRequest
from aion_brain.run_supervision.compensation import CompensationPlanner
from aion_brain.run_supervision.control import RunControlService
from aion_brain.run_supervision.reports import RunSupervisionReportService
from aion_brain.run_supervision.repository import RunSupervisionRepository
from aion_brain.run_supervision.service import RunSupervisionService
from aion_brain.run_supervision.status_sampler import RunStatusSampler
from aion_brain.run_supervision.targets import RunTargetStatusAdapter
from aion_brain.run_supervision.timeouts import TimeoutPolicyService

SCOPE = ["workspace:main"]


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=["test"],
            audit_level="standard",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeActionProposalService:
    def __init__(self) -> None:
        self.payloads: list[object] = []

    def create_proposal(self, request: object) -> SimpleNamespace:
        self.payloads.append(request)
        return SimpleNamespace(action_proposal_id=f"proposal-{len(self.payloads)}")


class FakeCommandBus:
    def __init__(self, status: str = "running") -> None:
        self.command = SimpleNamespace(
            command_id="command-1",
            status=status,
            progress={},
            error={},
            result={},
        )

    def get(self, command_id: str) -> object:
        return self.command

    def cancel(self, command_id: str, reason: str) -> object:
        self.command.status = "cancelled"
        self.command.error = {"reason": reason}
        return self.command


class FakeWorkflowService:
    def __init__(self, status: str = "failed") -> None:
        self.run = SimpleNamespace(workflow_run_id="workflow-run-1", status=status)

    def get_run(self, workflow_run_id: str, scope: list[str]) -> object:
        return self.run

    def cancel_run(self, request: object) -> object:
        self.run.status = "cancelled"
        return self.run

    def pause_run(self, request: object) -> object:
        self.run.status = "paused"
        return self.run

    def resume_run(self, request: object) -> object:
        self.run.status = "running"
        return self.run


class RunFixture:
    def __init__(self, policy: object | None = None) -> None:
        self.settings = Settings(
            _env_file=None,
            DATABASE_URL="sqlite+pysqlite:///:memory:",
            AION_RUN_SUPERVISION_DEFAULT_STALL_SECONDS=1,
        )
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.repository = RunSupervisionRepository(engine=engine)
        self.policy = policy or AllowPolicy()
        self.telemetry = FakeTelemetry()
        self.action_proposals = FakeActionProposalService()
        self.adapter = RunTargetStatusAdapter(
            command_bus=FakeCommandBus(),
            workflow_service=FakeWorkflowService(),
        )
        self.supervision = RunSupervisionService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.sampler = RunStatusSampler(
            self.repository,
            self.adapter,
            self.policy,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.timeouts = TimeoutPolicyService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.control = RunControlService(
            self.repository,
            self.adapter,
            self.policy,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.compensation = CompensationPlanner(
            self.repository,
            self.policy,
            action_proposal_service=self.action_proposals,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.reports = RunSupervisionReportService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )


def run_request(**overrides: Any) -> RunSupervisionCreateRequest:
    payload: dict[str, Any] = {
        "source_type": "generic",
        "source_id": "source-1",
        "target_system": "command_bus",
        "target_run_id": "command-1",
        "run_type": "command",
        "owner_scope": SCOPE,
        "title": "Supervise command",
        "description": "Observe a command run.",
        "cancellable": True,
        "compensation_available": True,
    }
    payload.update(overrides)
    return RunSupervisionCreateRequest(**payload)


def old_datetime() -> datetime:
    return datetime.now(UTC) - timedelta(seconds=10)
