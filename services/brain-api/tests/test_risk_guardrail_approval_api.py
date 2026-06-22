"""Risk, guardrail, and approval API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.approvals import get_approval_service
from aion_brain.api.guardrails import get_guardrail_engine
from aion_brain.api.risk import get_risk_engine
from aion_brain.contracts.approvals import (
    ApprovalCreateRequest,
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalInboxQuery,
    ApprovalRequest,
)
from aion_brain.contracts.guardrails import (
    GuardrailDecision,
    GuardrailRule,
    RiskGuardrailEvaluation,
)
from aion_brain.contracts.risk import RiskAssessment
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app


def test_risk_guardrail_and_approval_apis_work_with_fakes() -> None:
    """API routes expose public AION contracts only."""
    risk = FakeRiskEngine()
    guardrails = FakeGuardrailEngine()
    approvals = FakeApprovalService()
    with overrides(risk, guardrails, approvals):
        client = TestClient(app)
        risk_response = client.post(
            "/brain/risk/assess",
            json={
                "action_type": "capability.invoke",
                "resource_type": "capability",
                "requested_risk_level": "high",
                "payload": {},
            },
        )
        evaluation = client.post(
            "/brain/risk/evaluate",
            json={
                "risk": {
                    "action_type": "capability.invoke",
                    "resource_type": "capability",
                    "requested_risk_level": "high",
                    "payload": {},
                }
            },
        )
        created_rule = client.post(
            "/brain/guardrails",
            json=guardrail_rule().model_dump(mode="json"),
        )
        listed_rules = client.get("/brain/guardrails")
        disabled_rule = client.post("/brain/guardrails/guardrail-1/disable")
        guardrail_decision = client.post(
            "/brain/guardrails/evaluate",
            json=risk_assessment().model_dump(mode="json"),
        )
        created_approval = client.post(
            "/brain/approvals",
            json={
                "action_type": "capability.invoke",
                "resource_type": "capability",
                "title": "Review",
                "description": "Review generic action.",
                "approval_scope": ["workspace:main"],
            },
        )
        inbox = client.get("/brain/approvals", params={"scope": "workspace:main"})
        fetched = client.get("/brain/approvals/approval-1", params={"scope": "workspace:main"})
        decided = client.post(
            "/brain/approvals/approval-1/decide",
            json={
                "approval_request_id": "ignored",
                "decision": "approve",
                "reason": "ok",
            },
        )
        cancelled = client.post("/brain/approvals/approval-1/cancel")
        expired = client.post("/brain/approvals/approval-1/expire")

    assert risk_response.status_code == 200
    assert risk_response.json()["decision"] == "require_approval"
    assert evaluation.status_code == 200
    assert evaluation.json()["final_decision"] == "require_approval"
    assert created_rule.status_code == 200
    assert listed_rules.json()[0]["guardrail_id"] == "guardrail-1"
    assert disabled_rule.json()["status"] == "disabled"
    assert guardrail_decision.json()["approval_required"] is True
    assert created_approval.json()["status"] == "pending"
    assert inbox.json()[0]["approval_request_id"] == "approval-1"
    assert fetched.json()["approval_request_id"] == "approval-1"
    assert decided.json()["decision"] == "approve"
    assert cancelled.json()["status"] == "cancelled"
    assert expired.json()["status"] == "expired"


class FakeRiskEngine:
    """Risk engine fake."""

    def assess(self, request: object) -> RiskAssessment:
        return risk_assessment()


class FakeGuardrailEngine:
    """Guardrail engine fake."""

    def create_rule(self, rule: GuardrailRule) -> GuardrailRule:
        return rule

    def list_rules(self, status: str | None = None) -> list[GuardrailRule]:
        return [guardrail_rule(status=status or "active")]

    def disable_rule(self, guardrail_id: str, *, actor_id: str | None = None) -> GuardrailRule:
        return guardrail_rule(status="disabled")

    def evaluate(self, risk: RiskAssessment) -> GuardrailDecision:
        return guardrail_decision()


class FakeApprovalService:
    """Approval service fake."""

    def evaluate_and_maybe_request(self, request: object) -> RiskGuardrailEvaluation:
        return RiskGuardrailEvaluation(
            risk_assessment=risk_assessment(),
            guardrail_decision=guardrail_decision(),
            approval_request=approval_request(),
            final_decision="require_approval",
            reason="approval_required",
            created_at=datetime.now(UTC),
        )

    def create_request(self, request: ApprovalCreateRequest) -> ApprovalRequest:
        return approval_request()

    def list_pending(self, query: ApprovalInboxQuery) -> list[ApprovalRequest]:
        return [approval_request()]

    def get_request(self, approval_request_id: str, scope: list[str]) -> ApprovalRequest | None:
        return approval_request()

    def decide(self, request: ApprovalDecisionRequest) -> ApprovalDecision:
        return ApprovalDecision(
            approval_decision_id="approval-decision-1",
            approval_request_id=request.approval_request_id,
            decision=request.decision,
            reason=request.reason,
            decision_payload={},
            created_at=datetime.now(UTC),
        )

    def cancel(
        self,
        approval_request_id: str,
        *,
        actor_id: str | None,
        reason: str,
    ) -> ApprovalRequest:
        return approval_request(status="cancelled")

    def expire(self, approval_request_id: str) -> ApprovalRequest:
        return approval_request(status="expired")


def overrides(
    risk: FakeRiskEngine,
    guardrails: FakeGuardrailEngine,
    approvals: FakeApprovalService,
) -> object:
    """Install dependency overrides."""

    class OverrideContext:
        def __enter__(self) -> None:
            app.dependency_overrides[get_risk_engine] = lambda: risk
            app.dependency_overrides[get_guardrail_engine] = lambda: guardrails
            app.dependency_overrides[get_approval_service] = lambda: approvals
            app.dependency_overrides[get_actor_context] = lambda: ActorContext(
                actor_id="actor-1",
                workspace_id="workspace-1",
                permissions=["risk.assess"],
                security_scope=["workspace:main"],
                dev_mode=True,
            )

        def __exit__(self, *args: object) -> None:
            app.dependency_overrides.clear()

    return OverrideContext()


def risk_assessment() -> RiskAssessment:
    """Return a risk assessment."""
    return RiskAssessment(
        risk_assessment_id="risk-1",
        trace_id="trace-1",
        action_type="capability.invoke",
        resource_type="capability",
        requested_risk_level="high",
        computed_risk_level="high",
        risk_score=0.8,
        factors=[],
        constraints=["approval_required"],
        decision="require_approval",
        metadata={"security_scope": ["workspace:main"]},
        created_at=datetime.now(UTC),
    )


def guardrail_decision() -> GuardrailDecision:
    """Return a guardrail decision."""
    return GuardrailDecision(
        guardrail_decision_id="guardrail-decision-1",
        trace_id="trace-1",
        risk_assessment_id="risk-1",
        action_type="capability.invoke",
        resource_type="capability",
        matched_guardrails=["guardrail-1"],
        allow=False,
        approval_required=True,
        blocked=False,
        severity="high",
        reason="guardrail_requires_approval",
        constraints=["approval_required"],
        metadata={},
        created_at=datetime.now(UTC),
    )


def guardrail_rule(status: str = "active") -> GuardrailRule:
    """Return a guardrail rule."""
    return GuardrailRule(
        guardrail_id="guardrail-1",
        name="Generic guardrail",
        description="Generic guardrail description.",
        status=status,  # type: ignore[arg-type]
        scope=["workspace:main"],
        action_types=["capability.invoke"],
        resource_types=["capability"],
        risk_levels=["high"],
        conditions={},
        effect="require_approval",
        severity="high",
        metadata={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def approval_request(status: str = "pending") -> ApprovalRequest:
    """Return an approval request."""
    return ApprovalRequest(
        approval_request_id="approval-1",
        trace_id="trace-1",
        action_type="capability.invoke",
        resource_type="capability",
        title="Review",
        description="Review generic action.",
        status=status,  # type: ignore[arg-type]
        priority="normal",
        approval_scope=["workspace:main"],
        payload={},
        constraints=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
