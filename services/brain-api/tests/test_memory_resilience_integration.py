"""Memory resilience integration tests."""

from __future__ import annotations

import pytest

from aion_brain.contracts.graph import GraphQuery, GraphQueryResult
from aion_brain.contracts.memory import SemanticMemoryQuery
from aion_brain.memory.graph_service import GraphMemoryService, GraphMemoryUnavailable
from aion_brain.memory.semantic_service import SemanticMemoryService, SemanticMemoryUnavailable
from tests.resilience_fakes import AllowPolicy
from tests.test_graph_memory_service import make_node
from tests.test_semantic_memory_service import FakeSemanticAdapter


def test_semantic_adapter_failure_enters_degraded_mode() -> None:
    degraded = FakeDegraded()
    service = SemanticMemoryService(
        adapter=FailingSemanticAdapter(),
        policy_adapter=AllowPolicy(),
        configured_adapter="turbovec",
        fallback_reason="local_fallback",
        degraded_mode_service=degraded,
    )

    with pytest.raises(SemanticMemoryUnavailable):
        service.retrieve(SemanticMemoryQuery(query="alpha", scope=["workspace:main"]))

    assert degraded.events[0]["component"] == "semantic_memory"
    assert degraded.events[0]["fallbacks_active"] == ["local_baseline"]


def test_graph_adapter_failure_enters_degraded_mode() -> None:
    degraded = FakeDegraded()
    service = GraphMemoryService(
        adapter=FailingGraphAdapter(),
        policy_adapter=AllowPolicy(),
        configured_adapter="graphiti",
        fallback_reason="local_fallback",
        degraded_mode_service=degraded,
    )

    with pytest.raises(GraphMemoryUnavailable):
        service.query_graph(GraphQuery(scope=["workspace:main"]))

    assert degraded.events[0]["component"] == "graph_memory"
    assert degraded.events[0]["fallbacks_active"] == ["local_baseline"]


class FakeDegraded:
    def __init__(self) -> None:
        self.events: list[dict[str, object]] = []

    def enter(self, **kwargs: object) -> object:
        self.events.append(kwargs)
        return kwargs


class FailingSemanticAdapter(FakeSemanticAdapter):
    adapter_name = "failing"

    def retrieve(self, query: SemanticMemoryQuery) -> list[object]:
        raise RuntimeError("semantic adapter unavailable")


class FailingGraphAdapter:
    adapter_name = "failing"

    def upsert_node(self, node: object) -> object:
        return object()

    def upsert_edge(self, edge: object) -> object:
        return object()

    def get_node(self, node_id: str, scope: list[str]) -> object | None:
        return make_node(node_id)

    def get_edge(self, edge_id: str, scope: list[str]) -> object | None:
        return None

    def query_graph(self, query: GraphQuery) -> GraphQueryResult:
        raise RuntimeError("graph adapter unavailable")

    def neighbors(
        self,
        node_id: str,
        scope: list[str],
        *,
        max_depth: int = 1,
        limit: int = 25,
    ) -> GraphQueryResult:
        raise RuntimeError("graph adapter unavailable")

    def soft_delete_node(self, node_id: str, scope: list[str]) -> bool:
        return True

    def soft_delete_edge(self, edge_id: str, scope: list[str]) -> bool:
        return True
