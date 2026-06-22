from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.responses import ResponseDraft
from aion_brain.contracts.situations import SituationCreateRequest
from aion_brain.contracts.temporal_state import StateAtomCreateRequest
from aion_brain.dialogue.repository import DialogueRepository
from aion_brain.responses.verifier import ResponseVerifier
from tests.kernel_fakes import AllowPolicy
from tests.situation_helpers import bundle


def test_response_verifier_warns_on_stale_state_atom_and_closed_situation() -> None:
    services = bundle()
    situation = services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Generic state.",
            owner_scope=["workspace:main"],
        )
    )
    closed = services.situation_service.close(
        situation.situation_id,
        ["workspace:main"],
        reason="done",
    )
    atom = services.state_atom_service.create(
        StateAtomCreateRequest(
            source_id="source-1",
            predicate="status",
            value={"status": "old"},
            status="stale",
            owner_scope=["workspace:main"],
        )
    )
    repository = DialogueRepository()
    response = repository.save_response(
        ResponseDraft(
            response_id="response-1",
            trace_id="trace-1",
            status="draft",
            response_type="answer",
            content="A generic response.",
            content_hash="hash",
            grounded=True,
            metadata={
                "owner_scope": ["workspace:main"],
                "situation_id": closed.situation_id,
                "state_atom_ids": [atom.state_atom_id],
            },
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
    )
    verifier = ResponseVerifier(
        repository,
        AllowPolicy(),
        situation_service=services.situation_service,
        state_atom_service=services.state_atom_service,
    )

    verification = verifier.verify(response.response_id)

    codes = {issue["code"] for issue in verification.issues}
    assert "state_atom_stale" in codes
    assert "situation_closed_as_current" in codes
    assert verification.status == "warning"
