"""Memory adapter interfaces."""

from typing import Any, Protocol

from aion_brain.contracts.memory import (
    MemoryRecord,
    MemoryType,
    SemanticIndexResponse,
    SemanticMemoryQuery,
    SemanticMemoryResult,
    TurboVecIndexStatus,
    TurboVecRebuildRequest,
    TurboVecRebuildResponse,
)


class LexicalMemoryAdapter(Protocol):
    """Interface for canonical lexical memory behavior."""

    def remember(self, record: MemoryRecord) -> str:
        """Store a memory record."""
        ...

    def retrieve(
        self,
        query: str,
        scope: list[str],
        limit: int = 10,
        memory_types: list[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """Retrieve memory records by query and scope."""
        ...

    def forget(self, memory_id: str) -> bool:
        """Forget a memory record."""
        ...


class SemanticMemoryAdapter(Protocol):
    """Interface for semantic recall engines."""

    adapter_name: str

    def remember(self, record: MemoryRecord) -> str:
        """Index a memory record semantically."""
        ...

    def retrieve(self, query: SemanticMemoryQuery) -> list[SemanticMemoryResult]:
        """Retrieve memory records by semantic similarity."""
        ...

    def forget(self, memory_id: str) -> bool:
        """Forget semantic vectors for a memory record."""
        ...

    def reindex(self, memory_id: str) -> SemanticIndexResponse:
        """Reindex one memory record."""
        ...

    def status(self, index_name: str = "default") -> TurboVecIndexStatus | None:
        """Return adapter status when supported."""
        ...

    def rebuild(self, request: TurboVecRebuildRequest) -> TurboVecRebuildResponse:
        """Rebuild adapter indexes when supported."""
        ...


class GraphMemoryAdapter(Protocol):
    """Interface for future graph memory engines."""

    def upsert_node(self, node: dict[str, Any]) -> str:
        """Upsert a graph node."""
        ...

    def upsert_edge(self, edge: dict[str, Any]) -> str:
        """Upsert a graph edge."""
        ...

    def query_graph(self, query: str, scope: list[str]) -> list[dict[str, Any]]:
        """Query graph memory."""
        ...
