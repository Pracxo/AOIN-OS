from __future__ import annotations

from aion_brain.contracts.outcomes import OutcomeCreateRequest, OutcomeQuery
from tests.outcome_helpers import bundle


def test_outcome_query_returns_matching_records() -> None:
    env = bundle()
    env.outcomes.create_outcome(
        OutcomeCreateRequest(
            source_type="command",
            source_id="command-1",
            outcome_type="command",
            title="Command outcome",
            summary="Observable result.",
            owner_scope=["workspace:main"],
        )
    )

    result = env.query.query(OutcomeQuery(scope=["workspace:main"], query="observable"))

    assert result.total_count == 1
    assert result.outcomes[0].source_id == "command-1"
