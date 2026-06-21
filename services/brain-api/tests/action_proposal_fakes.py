"""Shared fakes for action proposal tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.action_proposals.blockers import ActionBlockerService
from aion_brain.action_proposals.handoffs import ExecutionHandoffService
from aion_brain.action_proposals.proposals import ActionProposalService
from aion_brain.action_proposals.repository import ActionProposalRepository
from aion_brain.action_proposals.reviews import ActionReviewService
from aion_brain.action_proposals.tool_intent_review import ToolIntentReviewService
from aion_brain.config import Settings
from aion_brain.contracts.action_proposals import ActionProposal, ActionProposalCreateRequest
from aion_brain.contracts.model_outputs import ToolIntentCandidate
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


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


class FakeToolIntentRepository:
    def __init__(self, intent: ToolIntentCandidate | None = None) -> None:
        self.intent = intent

    def get_tool_intent(self, tool_intent_id: str) -> ToolIntentCandidate | None:
        if self.intent and self.intent.tool_intent_id == tool_intent_id:
            return self.intent
        return None


class DenyingGate:
    def decide(self, proposal: ActionProposal) -> dict[str, bool]:
        return {"allow": False}

    def assess(self, proposal: ActionProposal) -> dict[str, bool]:
        return {"allow": False}


class ActionFixture:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        policy: object | None = None,
        tool_intent_repository: object | None = None,
    ) -> None:
        self.settings = settings or Settings(
            _env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"
        )
        self.policy = policy or AllowPolicy()
        engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.repository = ActionProposalRepository(engine=engine)
        self.telemetry = FakeTelemetry()
        self.blockers = ActionBlockerService(
            self.repository,
            self.policy,
            telemetry_service=self.telemetry,
        )
        self.proposals = ActionProposalService(
            self.repository,
            self.policy,
            blocker_service=self.blockers,
            tool_intent_repository=tool_intent_repository,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.tool_reviews = ToolIntentReviewService(
            self.repository,
            tool_intent_repository or FakeToolIntentRepository(),
            self.policy,
            action_proposal_service=self.proposals,
            blocker_service=self.blockers,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )
        self.reviews = ActionReviewService(
            self.repository,
            self.policy,
            blocker_service=self.blockers,
            telemetry_service=self.telemetry,
        )
        self.handoffs = ExecutionHandoffService(
            self.repository,
            self.policy,
            blocker_service=self.blockers,
            telemetry_service=self.telemetry,
            settings=self.settings,
        )


def proposal_request(**overrides: object) -> ActionProposalCreateRequest:
    payload = {
        "source_type": "user_request",
        "source_id": "source-1",
        "proposal_type": "command",
        "title": "Review generic action",
        "description": "Operator review required.",
        "action_type": "generic",
        "target_type": "noop",
        "owner_scope": ["workspace:main"],
        "risk_level": "medium",
    }
    payload.update(overrides)
    return ActionProposalCreateRequest(**payload)


def tool_intent(**overrides: object) -> ToolIntentCandidate:
    payload = {
        "tool_intent_id": "tool-intent-1",
        "model_output_id": "model-output-1",
        "trace_id": "trace-1",
        "status": "captured",
        "intent_type": "command_dispatch",
        "tool_name": "generic",
        "action_type": "generic",
        "target_type": "noop",
        "arguments_redacted": {"value": "ok"},
        "risk_level": "medium",
        "blocked_reason": "captured_for_review",
    }
    payload.update(overrides)
    return ToolIntentCandidate(**payload)
