from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.responses import ResponseComposeRequest, ResponseDraft
from aion_brain.dialogue.repository import DialogueRepository
from aion_brain.responses.composer import ResponseComposer
from aion_brain.responses.verifier import ResponseVerifier
from tests.kernel_fakes import AllowPolicy


def test_response_composer_summarizes_recommendation_without_execution_wording() -> None:
    repository = DialogueRepository()
    composer = ResponseComposer(repository, AllowPolicy())

    draft = composer.compose(
        ResponseComposeRequest(
            trace_id="trace-1",
            goal="choose",
            context={},
            metadata={
                "owner_scope": ["workspace:main"],
                "decision_recommendation": {
                    "recommended_option_title": "retrieve more context",
                    "constraints": ["approval_required"],
                },
            },
        )
    )

    assert "recommendation, not execution" in draft.content
    assert "executed" not in draft.content.lower()


def test_response_verifier_flags_execution_claim_from_decision() -> None:
    repository = DialogueRepository()
    response = repository.save_response(
        ResponseDraft(
            response_id="response-1",
            trace_id="trace-1",
            status="draft",
            response_type="answer",
            content="The decision was executed.",
            content_hash="hash",
            grounded=True,
            metadata={
                "owner_scope": ["workspace:main"],
                "decision_recommendation": {"recommended_option_id": "option-1"},
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    verifier = ResponseVerifier(repository, AllowPolicy())

    verification = verifier.verify(response.response_id)

    assert any(issue["code"] == "decision_claimed_execution" for issue in verification.issues)
