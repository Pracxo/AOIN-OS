from __future__ import annotations

from datetime import timedelta

from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.contracts.situations import SituationCreateRequest
from aion_brain.contracts.temporal_state import TemporalStateWindowRequest
from aion_brain.retrieval.router import RetrievalRouter
from tests.kernel_fakes import AllowPolicy
from tests.situation_helpers import bundle, now


def test_retrieval_router_collects_situation_and_temporal_state() -> None:
    services = bundle()
    services.situation_service.create(
        SituationCreateRequest(
            title="Current state",
            summary="Alpha generic state.",
            owner_scope=["workspace:main"],
        )
    )
    timestamp = now()
    services.temporal_window_service.create(
        TemporalStateWindowRequest(
            owner_scope=["workspace:main"],
            start_at=timestamp - timedelta(hours=1),
            end_at=timestamp,
            summary="Alpha temporal state.",
        )
    )
    router = RetrievalRouter(
        policy_adapter=AllowPolicy(),
        situation_service=services.situation_service,
        temporal_state_window_service=services.temporal_window_service,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-situation",
            trace_id=None,
            intent_id=None,
            query="alpha",
            scope=["workspace:main"],
            requested_sources=["situation_model", "temporal_state"],
            limit=10,
        )
    )

    assert {item.source for item in result.items} == {"situation_model", "temporal_state"}
