from __future__ import annotations

from aion_brain.contracts.responses import (
    ResponseComposeRequest,
    ResponseDraft,
    ResponseVerification,
)
from aion_brain.responses.verifier import ResponseVerifier
from tests.dialogue_helpers import AllowPolicy, service_bundle


class HiddenReasoningRepository:
    def __init__(self) -> None:
        self.verification: ResponseVerification | None = None

    def get_response(self, response_id: str) -> ResponseDraft:
        return ResponseDraft.model_construct(
            response_id=response_id,
            status="draft",
            response_type="answer",
            content="hidden_reasoning: internal",
            content_hash="hash",
            grounded=False,
            grounding_refs=[],
            memory_refs=[],
            evidence_refs=[],
            clarification_refs=[],
            constraints=[],
            metadata={"owner_scope": ["workspace:main"]},
        )

    def save_verification(self, verification: ResponseVerification) -> ResponseVerification:
        self.verification = verification
        return verification

    def save_response(self, response: ResponseDraft) -> ResponseDraft:
        return response


def test_response_verifier_fails_response_with_hidden_reasoning_marker() -> None:
    repository = HiddenReasoningRepository()
    verifier = ResponseVerifier(repository, AllowPolicy())  # type: ignore[arg-type]

    verification = verifier.verify("response-1")

    assert verification.status == "failed"
    assert any(issue["code"] == "hidden_reasoning_present" for issue in verification.issues)


def test_response_verifier_passes_grounded_response() -> None:
    bundle = service_bundle()
    response = bundle.response_composer.compose(
        ResponseComposeRequest(context={"evidence_refs": ["evidence-1"]})
    )

    verification = bundle.response_verifier.verify(response.response_id)

    assert verification.status == "passed"
    assert verification.score == 1.0


def test_response_verifier_marks_blocked_response() -> None:
    bundle = service_bundle()
    response = bundle.response_composer.compose(ResponseComposeRequest(require_grounding=True))

    verification = bundle.response_verifier.verify(response.response_id)

    assert verification.status == "blocked"
