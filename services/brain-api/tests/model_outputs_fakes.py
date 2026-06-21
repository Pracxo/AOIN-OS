"""Shared fakes for model output governance tests."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.model_outputs.governance import OutputGovernanceService
from aion_brain.model_outputs.parser import OutputParser
from aion_brain.model_outputs.repository import ModelOutputRepository
from aion_brain.model_outputs.response_candidates import ResponseCandidateService
from aion_brain.model_outputs.structured_validator import StructuredOutputValidator
from aion_brain.model_outputs.tool_intents import ToolIntentCaptureService
from aion_brain.model_outputs.unsafe_detector import UnsafeOutputDetector


class AllowPolicy:
    """Always-allow policy fake."""

    def __init__(self) -> None:
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy(AllowPolicy):
    """Deny one policy action."""

    def __init__(self, action_type: str) -> None:
        super().__init__()
        self._action_type = action_type

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type != self._action_type
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=not allow,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["denied"],
            audit_level="standard" if allow else "high",
        )


class FakeTelemetry:
    """Collect visual telemetry events."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


class FakeSettings:
    """Small settings fake for governance tests."""

    model_outputs_enabled = True
    output_governance_enabled = True
    model_output_store_raw = False
    tool_intent_capture_enabled = True
    tool_intent_execution_enabled = False
    output_governance_require_grounding_default = False
    output_governance_block_tool_intents_default = True


def repository() -> ModelOutputRepository:
    """Return an in-memory model output repository."""

    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ModelOutputRepository(engine=engine)


def governance_service(
    *,
    policy: AllowPolicy | None = None,
    telemetry: FakeTelemetry | None = None,
) -> tuple[OutputGovernanceService, ModelOutputRepository, AllowPolicy, FakeTelemetry]:
    """Return a local governance service graph."""

    repo = repository()
    selected_policy = policy or AllowPolicy()
    selected_telemetry = telemetry or FakeTelemetry()
    detector = UnsafeOutputDetector()
    parser = OutputParser(detector)
    validator = StructuredOutputValidator(repo, detector, telemetry_service=selected_telemetry)
    candidates = ResponseCandidateService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
    )
    tool_intents = ToolIntentCaptureService(
        repo,
        selected_policy,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    service = OutputGovernanceService(
        repo,
        selected_policy,
        parser=parser,
        unsafe_detector=detector,
        structured_validator=validator,
        response_candidate_service=candidates,
        tool_intent_service=tool_intents,
        telemetry_service=selected_telemetry,
        settings=FakeSettings(),
    )
    return service, repo, selected_policy, selected_telemetry
