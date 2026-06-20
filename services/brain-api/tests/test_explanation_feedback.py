from __future__ import annotations

from aion_brain.contracts.explanations import ExplanationFeedback
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.explanations.feedback import ExplanationFeedbackService
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


def test_feedback_service_records_feedback() -> None:
    service = ExplanationFeedbackService(ExplanationRepository(), AllowPolicy())

    feedback = service.create_feedback(
        ExplanationFeedback(
            explanation_feedback_id="feedback-1",
            explanation_id="explanation-1",
            feedback_type="helpful",
            rating=5,
            metadata={"owner_scope": ["workspace:main"]},
        )
    )

    assert feedback.created_at is not None
    assert service.list_feedback(explanation_id="explanation-1")[0].rating == 5
