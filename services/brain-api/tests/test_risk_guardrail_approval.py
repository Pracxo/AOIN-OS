"""Risk, guardrail, and approval control-plane tests."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from aion_brain.approvals.repository import ApprovalRepository
from aion_brain.approvals.service import ApprovalService
from aion_brain.approvals.state_machine import can_transition_approval
from aion_brain.config import Settings
from aion_brain.contracts.approvals import (
    ApprovalCreateRequest,
    ApprovalDecisionRequest,
    ApprovalInboxQuery,
    ApprovalRequest,
)
from aion_brain.contracts.guardrails import GuardrailRule, RiskGuardrailEvaluationRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.risk import RiskAssessmentRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.guardrails.engine import GuardrailEngine
from aion_brain.guardrails.repository import GuardrailRepository
from aion_brain.risk.engine import RiskEngine, calculate_risk_score, computed_risk_level
from aion_brain.risk.repository import RiskRepository


class AllowPolicy:
    """Policy fake that records requests."""

    def __init__(self, *, allow: bool = True) -> None:
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
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard" if self.allow else "high",
        )


class FakeTelemetry:
    """Collect visual telemetry."""

    def __init__(self) -> None:
        self.events: list[VisualTelemetryEvent] = []

    def emit(self, event: VisualTelemetryEvent) -> None:
        self.events.append(event)


def test_risk_contract_rejects_secret_like_payload_keys() -> None:
    """Risk payloads must not store secrets."""
    with pytest.raises(ValueError, match="secret-like"):
        RiskAssessmentRequest(
            action_type="capability.invoke",
            resource_type="capability",
            requested_risk_level="medium",
            payload={"api_key": "hidden"},
        )


def test_guardrail_contract_rejects_domain_specific_terms() -> None:
    """Guardrail rules stay generic."""
    with pytest.raises(ValueError, match="domain-neutral"):
        guardrail_rule(action_types=["finance.analyze"])


def test_approval_contract_rejects_secret_payload_keys() -> None:
    """Approval payloads must not contain secrets."""
    with pytest.raises(ValueError, match="secret-like"):
        approval_request(payload={"token": "hidden"})


def test_approval_state_machine_allows_only_pending_to_terminal() -> None:
    """Approval status transitions are strict."""
    assert can_transition_approval("pending", "approved") is True
    assert can_transition_approval("pending", "expired") is True
    assert can_transition_approval("approved", "denied") is False


def test_risk_engine_scores_factors_and_persists_assessment() -> None:
    """RiskEngine computes score, requires approval, persists, and emits telemetry."""
    engine, risk_repository, _, _, telemetry, policy = services()
    request = risk_request(
        context={
            "controlled_execution": True,
            "invokes_capability": True,
            "approval_present": False,
            "security_scope": ["workspace:main"],
        }
    )

    assessment = engine.assess(request)

    assert assessment.computed_risk_level == "high"
    assert assessment.decision == "require_approval"
    assert risk_repository.get_assessment(assessment.risk_assessment_id) == assessment
    assert telemetry.events[-1].event_type == "risk_assessed"
    assert policy.requests[-1].action_type == "risk.assess"


def test_risk_score_helpers_are_deterministic() -> None:
    """Risk score helper maps thresholds predictably."""
    score, factors = calculate_risk_score(
        risk_request(requested_risk_level="medium", context={"dry_run": True})
    )

    assert score == pytest.approx(0.25)
    assert factors[-1]["factor"] == "dry_run"
    assert computed_risk_level(0.84) == "high"
    assert computed_risk_level(0.85) == "critical"


def test_guardrail_engine_uses_default_rules_and_records_decision() -> None:
    """GuardrailEngine applies default generic rules without Docker."""
    risk_engine, _, guardrail_engine, guardrail_repository, telemetry, _ = services()
    assessment = risk_engine.assess(
        risk_request(
            context={
                "mode": "controlled",
                "approval_present": False,
                "external_effect_possible": True,
                "security_scope": ["workspace:main"],
            }
        )
    )
    decision = guardrail_engine.evaluate(
        assessment.model_copy(
            update={
                "metadata": {
                    "mode": "controlled",
                    "approval_present": False,
                    "external_effect_possible": True,
                    "security_scope": ["workspace:main"],
                }
            }
        )
    )

    assert decision.approval_required is True
    assert "guardrail-external-effect-approval" in decision.matched_guardrails
    assert guardrail_repository.list_rules(status="active")
    assert telemetry.events[-1].event_type == "guardrail_evaluated"


def test_guardrail_policy_deny_fails_closed() -> None:
    """Policy denial blocks guardrail evaluation."""
    engine, _, guardrail_engine, _, _, _ = services(policy=AllowPolicy(allow=False))
    assessment = engine.assess(risk_request())

    decision = guardrail_engine.evaluate(assessment)

    assert decision.blocked is True
    assert decision.reason == "denied"


def test_approval_service_lifecycle_and_inbox() -> None:
    """ApprovalService creates, lists, decides, and blocks invalid re-decisions."""
    _, _, _, _, _, _, approval_service = services(with_approval=True)
    created = approval_service.create_request(
        ApprovalCreateRequest(
            action_type="capability.invoke",
            resource_type="capability",
            title="Review generic action",
            description="Review generic action before execution.",
            approval_scope=["workspace:main"],
            payload={"value": "ok"},
        )
    )

    inbox = approval_service.list_pending(ApprovalInboxQuery(scope=["workspace:main"]))
    decision = approval_service.decide(
        ApprovalDecisionRequest(
            approval_request_id=created.approval_request_id,
            decided_by="reviewer-1",
            decision="approve",
            reason="acceptable",
        )
    )

    fetched = approval_service.get_request(created.approval_request_id, ["workspace:main"])

    assert inbox[0].approval_request_id == created.approval_request_id
    assert decision.decision == "approve"
    assert fetched is not None
    assert fetched.status == "approved"
    with pytest.raises(ValueError, match="invalid_approval_transition"):
        approval_service.decide(
            ApprovalDecisionRequest(
                approval_request_id=created.approval_request_id,
                decision="deny",
                reason="too late",
            )
        )


def test_evaluate_and_maybe_request_creates_approval_for_elevated_action() -> None:
    """Combined evaluation creates approval and does not approve execution."""
    _, _, _, _, telemetry, _, approval_service = services(with_approval=True)

    evaluation = approval_service.evaluate_and_maybe_request(
        RiskGuardrailEvaluationRequest(
            risk=risk_request(
                requested_risk_level="high",
                context={
                    "approval_present": False,
                    "security_scope": ["workspace:main"],
                },
            )
        )
    )

    assert evaluation.final_decision == "require_approval"
    assert evaluation.approval_request is not None
    assert evaluation.approval_request.status == "pending"
    assert "approval_created" in [event.event_type for event in telemetry.events]


def services(*, policy: AllowPolicy | None = None, with_approval: bool = False):
    """Create in-memory risk, guardrail, and optional approval services."""
    engine = sqlite_engine()
    selected_policy = policy or AllowPolicy()
    telemetry = FakeTelemetry()
    settings = Settings(_env_file=None)
    risk_repository = RiskRepository(engine=engine)
    guardrail_repository = GuardrailRepository(engine=engine)
    risk_engine = RiskEngine(
        repository=risk_repository,
        policy_adapter=selected_policy,
        telemetry_service=telemetry,
        settings=settings,
    )
    guardrail_engine = GuardrailEngine(
        repository=guardrail_repository,
        policy_adapter=selected_policy,
        telemetry_service=telemetry,
        settings=settings,
    )
    if with_approval:
        approval_service = ApprovalService(
            repository=ApprovalRepository(engine=engine),
            risk_engine=risk_engine,
            guardrail_engine=guardrail_engine,
            policy_adapter=selected_policy,
            telemetry_service=telemetry,
            settings=settings,
        )
        return (
            risk_engine,
            risk_repository,
            guardrail_engine,
            guardrail_repository,
            telemetry,
            selected_policy,
            approval_service,
        )
    return (
        risk_engine,
        risk_repository,
        guardrail_engine,
        guardrail_repository,
        telemetry,
        selected_policy,
    )


def sqlite_engine() -> Engine:
    """Create a shared in-memory SQLite engine."""
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def risk_request(
    *,
    requested_risk_level: str = "medium",
    context: dict[str, object] | None = None,
) -> RiskAssessmentRequest:
    """Create a generic risk request."""
    return RiskAssessmentRequest(
        trace_id="trace-1",
        actor_id="actor-1",
        workspace_id="workspace-1",
        action_type="capability.invoke",
        resource_type="capability",
        resource_id="capability-1",
        requested_risk_level=requested_risk_level,  # type: ignore[arg-type]
        payload={"value": "ok"},
        context=context or {"security_scope": ["workspace:main"]},
        metadata={"security_scope": ["workspace:main"]},
    )


def guardrail_rule(
    *,
    action_types: list[str] | None = None,
) -> GuardrailRule:
    """Create a generic guardrail rule."""
    return GuardrailRule(
        guardrail_id="guardrail-1",
        name="Generic guardrail",
        description="Generic guardrail description.",
        status="active",
        scope=["workspace:main"],
        action_types=action_types or ["capability.invoke"],
        resource_types=["capability"],
        risk_levels=["medium"],
        conditions={},
        effect="require_approval",
        severity="medium",
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def approval_request(payload: dict[str, object] | None = None) -> ApprovalRequest:
    """Create an approval request."""
    return ApprovalRequest(
        approval_request_id="approval-1",
        action_type="capability.invoke",
        resource_type="capability",
        title="Review generic action",
        description="Review generic action before execution.",
        status="pending",
        priority="normal",
        approval_scope=["workspace:main"],
        payload=payload or {},
        constraints=[],
    )
