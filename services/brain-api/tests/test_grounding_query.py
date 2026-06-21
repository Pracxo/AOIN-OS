from __future__ import annotations

from aion_brain.contracts.grounding import GroundingQuery
from tests.grounding_helpers import service_bundle, source


def test_grounding_query_returns_contracts() -> None:
    bundle = service_bundle()
    bundle.repository.save_source(source())

    result = bundle.query.query(GroundingQuery(scope=["workspace:main"]))

    assert result.sources
    assert result.total_count >= 1
