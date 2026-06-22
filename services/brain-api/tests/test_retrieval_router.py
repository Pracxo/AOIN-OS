"""Retrieval Router tests."""

from datetime import UTC, datetime

from aion_brain.contracts.memory import (
    MemoryRecord,
    MemoryRetrievalRequest,
    SemanticMemoryQuery,
    SemanticMemoryResult,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.retrieval import RetrievalRequest, RetrievalResult
from aion_brain.retrieval.router import RetrievalRouter


class FakePolicyAdapter:
    """Policy fake for retrieval tests."""

    def __init__(self, *, deny_actions: set[str] | None = None, deny_all: bool = False) -> None:
        self.deny_actions = deny_actions or set()
        self.deny_all = deny_all
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = not self.deny_all and request.action_type not in self.deny_actions
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard",
        )


class FakeMemoryService:
    """Lexical memory fake."""

    def __init__(self, *, fail: bool = False, duplicate: bool = False) -> None:
        self.fail = fail
        self.duplicate = duplicate
        self.requests: list[MemoryRetrievalRequest] = []

    def retrieve(self, request: MemoryRetrievalRequest) -> list[MemoryRecord]:
        self.requests.append(request)
        if self.fail:
            raise RuntimeError("source failed")
        records = [make_memory("memory-1")]
        if self.duplicate:
            records.append(make_memory("memory-1"))
        return records


class FakeSemanticMemoryService:
    """Semantic memory fake."""

    def __init__(self) -> None:
        self.requests: list[SemanticMemoryQuery] = []

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        self.requests.append(query)
        return [
            SemanticMemoryResult(
                memory=make_memory("memory-1"),
                score=0.91,
                retrieval_source="semantic_memory",
                adapter_name="turbovec",
                matched_terms=["alpha"],
                metadata={"index_name": "default"},
            )
        ]


class FakeTelemetryService:
    """Telemetry fake."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def save_visual_telemetry(self, trace_id: str, events: list[object]) -> list[object]:
        self.events.extend(events)
        return events


class FakeRetrievalRepository:
    """Retrieval repository fake."""

    def __init__(self) -> None:
        self.saved: RetrievalResult | None = None

    def save(self, result: RetrievalResult, **kwargs: object) -> RetrievalResult:
        self.saved = result
        return result


class FakeCapabilityRegistry:
    """Capability registry fake."""

    def list_manifests(self) -> list[object]:
        return [
            type(
                "Manifest",
                (),
                {
                    "module_id": "test.module",
                    "capabilities": [
                        {
                            "capability_id": "test.echo",
                            "name": "Echo",
                            "description": "Echo generic input",
                        }
                    ],
                },
            )()
        ]


def test_retrieval_router_calls_policy_before_memory_retrieval() -> None:
    """Router authorizes before calling memory retrieval."""
    policy = FakePolicyAdapter()
    memory = FakeMemoryService()
    router = RetrievalRouter(policy_adapter=policy, memory_service=memory)

    result = router.retrieve(make_request(["lexical_memory"]))

    assert result.items[0].source_id == "memory-1"
    assert policy.requests[0].action_type == "memory.retrieve"
    assert memory.requests[0].query == "alpha"


def test_policy_deny_for_all_sources_returns_empty_result_with_constraints() -> None:
    """Global policy denial fails closed for retrieval."""
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(deny_all=True),
        memory_service=FakeMemoryService(),
    )

    result = router.retrieve(make_request(["lexical_memory"]))

    assert result.items == []
    assert "source_blocked_by_policy:all" in result.constraints


def test_policy_deny_for_one_source_continues_with_allowed_sources() -> None:
    """A source-level policy block does not stop other sources."""
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(deny_actions={"capability.list"}),
        memory_service=FakeMemoryService(),
        capability_registry=FakeCapabilityRegistry(),
    )

    result = router.retrieve(make_request(["lexical_memory", "capability_registry"]))

    assert [item.source for item in result.items] == ["lexical_memory"]
    assert "source_blocked_by_policy:capability_registry" in result.constraints


def test_source_failure_adds_source_unavailable_constraint() -> None:
    """Source exceptions become constraints."""
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        memory_service=FakeMemoryService(fail=True),
    )

    result = router.retrieve(make_request(["lexical_memory"]))

    assert result.items == []
    assert "source_unavailable:lexical_memory" in result.constraints


def test_retrieval_router_deduplicates_same_source_id() -> None:
    """Duplicate source IDs collapse into one selected item."""
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        memory_service=FakeMemoryService(duplicate=True),
    )

    result = router.retrieve(make_request(["lexical_memory"]))

    assert [item.source_id for item in result.items] == ["memory-1"]


def test_retrieval_router_emits_telemetry_for_selected_items() -> None:
    """Selected retrieval items emit visual telemetry."""
    telemetry = FakeTelemetryService()
    repository = FakeRetrievalRepository()
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        memory_service=FakeMemoryService(),
        telemetry_service=telemetry,
        retrieval_repository=repository,
    )

    result = router.retrieve(make_request(["lexical_memory"]))

    assert result.items
    assert len(telemetry.events) == 1
    assert repository.saved is result


def test_retrieval_router_preserves_semantic_adapter_metadata() -> None:
    """Semantic source items carry adapter metadata for downstream context."""
    semantic_memory = FakeSemanticMemoryService()
    router = RetrievalRouter(
        policy_adapter=FakePolicyAdapter(),
        semantic_memory_service=semantic_memory,
    )

    result = router.retrieve(make_request(["semantic_memory"]))

    assert result.items[0].source == "semantic_memory"
    assert result.items[0].metadata["adapter_name"] == "turbovec"
    assert result.items[0].metadata["retrieval_source"] == "semantic_memory"
    assert semantic_memory.requests[0].query == "alpha"


def make_request(sources: list[str]) -> RetrievalRequest:
    """Create a retrieval request."""
    return RetrievalRequest(
        retrieval_id="retrieval-1",
        trace_id="trace-1",
        intent_id="intent-1",
        query="alpha",
        scope=["workspace:main"],
        requested_sources=sources,
        limit=10,
    )


def make_memory(memory_id: str) -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id=memory_id,
        memory_type="semantic",
        owner_scope=["workspace:main"],
        source_event_id=None,
        content_ref="content://memory-1",
        summary="alpha beta",
        confidence=0.9,
        sensitivity="low",
        created_at=datetime.now(UTC),
        expires_at=None,
        metadata={},
    )
