from __future__ import annotations

from aion_brain.contracts.responses import ResponseDraft, ResponseVerification
from aion_brain.responses.verifier import ResponseVerifier
from tests.belief_helpers import belief_bundle, create_claim
from tests.dialogue_helpers import AllowPolicy


class BeliefResponseRepository:
    def __init__(self, response: ResponseDraft) -> None:
        self.response = response

    def get_response(self, response_id: str) -> ResponseDraft:
        return self.response

    def save_verification(self, verification: ResponseVerification) -> ResponseVerification:
        return verification

    def save_response(self, response: ResponseDraft) -> ResponseDraft:
        self.response = response
        return response


def test_response_verifier_warns_for_contradicted_belief_reference() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "A referenced claim can be contradicted.")
    bundle.repository.save_claim(claim.model_copy(update={"status": "contradicted"}))
    response = ResponseDraft.model_construct(
        response_id="response-1",
        status="draft",
        response_type="answer",
        content="A local answer.",
        content_hash="hash",
        grounded=True,
        grounding_refs=[],
        memory_refs=[],
        evidence_refs=[],
        clarification_refs=[],
        constraints=[],
        metadata={"owner_scope": ["workspace:main"], "belief_refs": [claim.claim_id]},
    )
    verifier = ResponseVerifier(
        BeliefResponseRepository(response),  # type: ignore[arg-type]
        AllowPolicy(),
        belief_service=bundle.service,
    )

    verification = verifier.verify("response-1")

    assert verification.status == "warning"
    assert any(issue["code"] == "belief_contradicted" for issue in verification.issues)


def test_response_verifier_flags_required_ungrounded_belief_reference() -> None:
    bundle = belief_bundle()
    claim = create_claim(bundle, "A referenced claim may lack evidence.")
    response = ResponseDraft.model_construct(
        response_id="response-1",
        status="draft",
        response_type="answer",
        content="A local answer.",
        content_hash="hash",
        grounded=True,
        grounding_refs=[],
        memory_refs=[],
        evidence_refs=[],
        clarification_refs=[],
        constraints=[],
        metadata={
            "owner_scope": ["workspace:main"],
            "belief_refs": [claim.claim_id],
            "require_grounding": True,
        },
    )
    verifier = ResponseVerifier(
        BeliefResponseRepository(response),  # type: ignore[arg-type]
        AllowPolicy(),
        belief_service=bundle.service,
    )

    verification = verifier.verify("response-1")

    assert any(issue["code"] == "belief_ungrounded" for issue in verification.issues)
