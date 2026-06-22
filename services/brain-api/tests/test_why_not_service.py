from __future__ import annotations

from aion_brain.contracts.explanations import WhyNotRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.explanations.repository import ExplanationRepository
from aion_brain.explanations.why_not import WhyNotService


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


def test_why_not_service_explains_metadata_blockers() -> None:
    service = WhyNotService(ExplanationRepository(), AllowPolicy())

    answer = service.answer(
        WhyNotRequest(
            trace_id="trace-1",
            question="Why did this not continue?",
            target_type="trace",
            target_id="trace-1",
            owner_scope=["workspace:main"],
            metadata={"approval_required": True, "approval_request_id": "approval-1"},
        )
    )

    assert answer.missing_requirements == ["approval_present"]
    assert answer.next_possible_steps == ["request_approval"]
    assert service.get(answer.why_not_id, ["workspace:main"]) is not None
