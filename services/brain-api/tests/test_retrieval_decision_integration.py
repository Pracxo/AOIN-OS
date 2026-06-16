from __future__ import annotations

from aion_brain.contracts.decisions import DecisionFrameCreateRequest, DecisionRecordRequest
from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.retrieval.router import RetrievalRouter
from tests.decision_helpers import bundle
from tests.kernel_fakes import AllowPolicy


def test_retrieval_router_includes_decision_journal_source() -> None:
    services = bundle()
    frame = services.frame_service.create_frame(
        DecisionFrameCreateRequest(
            title="Choose",
            question="Which option?",
            owner_scope=["workspace:main"],
        )
    )
    services.journal.record_decision(
        DecisionRecordRequest(
            decision_frame_id=frame.decision_frame_id,
            rationale="Record only.",
        )
    )
    router = RetrievalRouter(
        policy_adapter=AllowPolicy(),
        decision_journal_service=services.journal,
    )

    result = router.retrieve(
        RetrievalRequest(
            retrieval_id="retrieval-decisions",
            trace_id=None,
            intent_id=None,
            query="choose",
            scope=["workspace:main"],
            requested_sources=["decision_journal"],
            limit=10,
        )
    )

    assert result.items
    assert {item.source for item in result.items} == {"decision_journal"}
