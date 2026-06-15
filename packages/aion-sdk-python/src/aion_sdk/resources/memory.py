"""Memory API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class MemoryResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, record: JSONDict) -> JSONValue:
        return self._client.post("/brain/memory", json=record)

    def get(self, memory_id: str) -> JSONValue:
        return self._client.get(f"/brain/memory/{memory_id}")

    def delete(self, memory_id: str) -> JSONValue:
        return self._client.delete(f"/brain/memory/{memory_id}")

    def retrieve(
        self,
        query: str,
        *,
        scope: list[str],
        limit: int = 10,
        memory_types: list[str] | None = None,
    ) -> JSONValue:
        return self._client.post(
            "/brain/memory/retrieve",
            json={
                "query": query,
                "scope": scope,
                "limit": limit,
                "memory_types": memory_types or [],
            },
        )

    def semantic_retrieve(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/memory/semantic/retrieve", json=request)

    def adapters(self) -> JSONValue:
        return self._client.get("/brain/memory/semantic/adapters")

    def governance_evaluate(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/memory/governance/evaluate", json=request)

