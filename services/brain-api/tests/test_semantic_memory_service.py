"""Semantic memory service tests."""

from datetime import UTC, datetime

import pytest

from aion_brain.contracts.memory import (
    MemoryRecord,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.memory.semantic_service import SemanticMemoryPolicyDenied, SemanticMemoryService


class FakePolicyAdapter:
    """Policy fake for semantic memory service tests."""

    def __init__(self, *, allow: bool = True) -> None:
        self.allow = allow
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        return PolicyDecision(
            decision_id="decision-1",
            trace_id=request.trace_id or "",
            allow=self.allow,
            approval_required=False,
            reason="allowed" if self.allow else "denied",
            constraints=[] if self.allow else ["blocked"],
            audit_level="standard",
        )


class FakeSemanticAdapter:
    """Semantic adapter fake."""

    def __init__(self) -> None:
        self.record = make_record()

    def remember(self, record: MemoryRecord) -> str:
        return f"fake-{record.memory_id}"

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        return [
            SemanticMemoryResult(
                memory=self.record,
                score=0.8,
                retrieval_source="semantic",
                adapter_name="fake",
                matched_terms=["alpha"],
                metadata={},
            )
        ]

    def forget(self, memory_id: str) -> bool:
        return True

    def reindex(self, memory_id: str) -> SemanticIndexResponse:
        return SemanticIndexResponse(
            indexed=True,
            memory_id=memory_id,
            adapter_name="fake",
            embedding_id=f"fake-{memory_id}",
            reason=None,
        )


def make_record() -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id="memory-1",
        memory_type="semantic",
        owner_scope=["workspace:main"],
        source_event_id=None,
        content_ref=None,
        summary="alpha beta",
        confidence=0.9,
        sensitivity="low",
        created_at=datetime.now(UTC),
        expires_at=None,
        metadata={},
    )


def test_semantic_memory_service_calls_policy_before_retrieve() -> None:
    """Semantic retrieval is policy-gated."""
    policy = FakePolicyAdapter()
    service = SemanticMemoryService(adapter=FakeSemanticAdapter(), policy_adapter=policy)

    results = service.retrieve(SemanticMemoryQuery(query="alpha", scope=["workspace:main"]))

    assert results[0].memory.memory_id == "memory-1"
    assert policy.requests[0].action_type == "memory.retrieve"


def test_policy_deny_blocks_semantic_retrieve() -> None:
    """Policy denial prevents semantic retrieval."""
    service = SemanticMemoryService(
        adapter=FakeSemanticAdapter(),
        policy_adapter=FakePolicyAdapter(allow=False),
    )

    with pytest.raises(SemanticMemoryPolicyDenied):
        service.retrieve(SemanticMemoryQuery(query="alpha", scope=["workspace:main"]))
