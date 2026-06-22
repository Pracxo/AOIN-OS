"""Concept registry SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConceptsResource:
    """Client helpers for concept registry APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/concepts", json=payload)

    def list_concepts(
        self,
        scope: list[str],
        *,
        query: str | None = None,
        concept_type: list[str] | None = None,
        status: str | None = "active",
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if query is not None:
            params["query"] = query
        if concept_type:
            params["concept_type"] = concept_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/concepts", params=params)

    def list(
        self,
        scope: builtins.list[str],
        *,
        query: str | None = None,
        concept_type: builtins.list[str] | None = None,
        status: str | None = "active",
        limit: int = 100,
    ) -> JSONValue:
        return self.list_concepts(
            scope,
            query=query,
            concept_type=concept_type,
            status=status,
            limit=limit,
        )

    def get(self, concept_id: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.get(f"/brain/concepts/{concept_id}", params={"scope": scope})

    def archive(self, concept_id: str, reason: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/concepts/{concept_id}/archive",
            params={"scope": scope},
            json={"reason": reason},
        )
