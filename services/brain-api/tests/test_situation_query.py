from __future__ import annotations

from aion_brain.contracts.situations import SituationCreateRequest, SituationQuery
from aion_brain.contracts.temporal_state import StateAtomCreateRequest
from tests.situation_helpers import bundle


def test_situation_query_can_include_state_atoms() -> None:
    services = bundle()
    situation = services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Generic searchable state.",
            owner_scope=["workspace:main"],
        )
    )
    services.state_atom_service.create(
        StateAtomCreateRequest(
            situation_id=situation.situation_id,
            source_id="source-1",
            predicate="status",
            value={"status": "active"},
            owner_scope=["workspace:main"],
        )
    )

    result = services.query_service.query(
        SituationQuery(
            scope=["workspace:main"],
            text="searchable",
            include_state_atoms=True,
            limit=10,
        )
    )

    assert result.total == 1
    assert result.state_atoms
