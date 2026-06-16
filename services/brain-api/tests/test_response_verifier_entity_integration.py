from __future__ import annotations

from typing import cast

from aion_brain.contracts.entities import EntityRecord
from aion_brain.contracts.responses import ResponseDraft, ResponseVerification
from aion_brain.responses.verifier import ResponseVerifier
from tests.dialogue_helpers import AllowPolicy
from tests.entity_helpers import create_entity, entity_bundle


class EntityResponseRepository:
    def __init__(self, response: ResponseDraft) -> None:
        self.response = response

    def get_response(self, response_id: str) -> ResponseDraft:
        return self.response

    def save_verification(self, verification: ResponseVerification) -> ResponseVerification:
        return verification

    def save_response(self, response: ResponseDraft) -> ResponseDraft:
        self.response = response
        return response


def test_response_verifier_warns_for_unresolved_entity_reference() -> None:
    response = _response({"entity_refs": ["entity-missing"]})
    verifier = ResponseVerifier(
        EntityResponseRepository(response),  # type: ignore[arg-type]
        AllowPolicy(),
        entity_service=entity_bundle().entity_service,
    )

    verification = verifier.verify("response-1")

    assert verification.status == "warning"
    assert any(issue["code"] == "entity_unresolved" for issue in verification.issues)


def test_response_verifier_requires_grounding_for_entity_reference() -> None:
    bundle = entity_bundle()
    entity = cast(EntityRecord, create_entity(bundle))
    response = _response(
        {
            "entity_refs": [entity.entity_id],
            "require_grounding": True,
        }
    )
    verifier = ResponseVerifier(
        EntityResponseRepository(response),  # type: ignore[arg-type]
        AllowPolicy(),
        entity_service=bundle.entity_service,
    )

    verification = verifier.verify("response-1")

    assert any(issue["code"] == "entity_ungrounded" for issue in verification.issues)


def _response(metadata: dict[str, object]) -> ResponseDraft:
    return ResponseDraft.model_construct(
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
        metadata={"owner_scope": ["workspace:main"], **metadata},
    )
