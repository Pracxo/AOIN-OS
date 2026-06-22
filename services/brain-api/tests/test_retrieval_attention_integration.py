"""Retrieval Router attention integration tests."""

from datetime import UTC, datetime

from aion_brain.contracts.retrieval import RetrievalRequest
from aion_brain.contracts.working_memory import WorkingMemoryQuery, WorkingMemorySlot
from aion_brain.retrieval.router import RetrievalRouter
from tests.kernel_fakes import AllowPolicy


class FakeWorkingMemoryService:
    def __init__(self) -> None:
        self.requests: list[WorkingMemoryQuery] = []

    def query_slots(self, query: WorkingMemoryQuery) -> list[WorkingMemorySlot]:
        self.requests.append(query)
        return [
            WorkingMemorySlot(
                slot_id="slot-1",
                focus_session_id=None,
                trace_id="trace-1",
                actor_id="actor-1",
                workspace_id="workspace-1",
                slot_type="recent_event",
                source_type="event",
                source_id="event-1",
                content={"event_id": "event-1"},
                summary="alpha beta",
                priority=0.6,
                confidence=0.8,
                ttl_seconds=None,
                expires_at=None,
                pinned=False,
                owner_scope=["workspace:main"],
                metadata={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                deleted_at=None,
            )
        ]


def test_retrieval_router_includes_working_memory_source() -> None:
    """RetrievalRouter converts working memory slots into context items."""
    working_memory = FakeWorkingMemoryService()
    router = RetrievalRouter(
        policy_adapter=AllowPolicy(),
        working_memory_service=working_memory,
    )

    result = router.retrieve(request(metadata={}))

    assert result.items[0].source == "working_memory"
    assert working_memory.requests[0].scope == ["workspace:main"]


def test_retrieval_router_boosts_attention_selected_slots() -> None:
    """Attention-selected slots receive a deterministic bounded boost."""
    router = RetrievalRouter(
        policy_adapter=AllowPolicy(),
        working_memory_service=FakeWorkingMemoryService(),
    )

    result = router.retrieve(request(metadata={"selected_slot_ids": ["slot-1"]}))

    assert result.items[0].score > 0.6
    assert result.items[0].metadata["attention_boost"] == 0.1


def request(metadata: dict[str, object]) -> RetrievalRequest:
    return RetrievalRequest(
        retrieval_id="retrieval-1",
        trace_id="trace-1",
        intent_id="intent-1",
        query="alpha",
        scope=["workspace:main"],
        requested_sources=["working_memory"],
        limit=10,
        metadata=metadata,
    )
