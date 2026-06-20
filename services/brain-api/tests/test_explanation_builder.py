from __future__ import annotations

import pytest

from aion_brain.contracts.explanations import ExplanationRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.explanations.builder import ExplanationBuilder
from aion_brain.explanations.repository import ExplanationRepository


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
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetry:
    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def test_explanation_builder_persists_grounded_explanation() -> None:
    telemetry = FakeTelemetry()
    builder = ExplanationBuilder(
        ExplanationRepository(),
        AllowPolicy(),
        telemetry_service=telemetry,
    )

    explanation = builder.explain(
        ExplanationRequest(
            trace_id="trace-1",
            explanation_type="generic",
            target_type="trace",
            target_id="trace-1",
            owner_scope=["workspace:main"],
            metadata={"evidence_refs": ["evidence-1"], "audit_refs": ["audit-1"]},
        )
    )

    assert explanation.status == "completed"
    assert explanation.grounded is True
    assert explanation.evidence_refs == ["evidence-1"]
    assert builder.get(explanation.explanation_id, ["workspace:main"]) is not None
    assert any(
        getattr(event, "event_type", "") == "explanation_created" for event in telemetry.events
    )


def test_explanation_builder_policy_deny_fails_closed() -> None:
    builder = ExplanationBuilder(ExplanationRepository(), DenyPolicy())

    with pytest.raises(PermissionError):
        builder.explain(
            ExplanationRequest(
                explanation_type="generic",
                target_type="trace",
                owner_scope=["workspace:main"],
            )
        )
