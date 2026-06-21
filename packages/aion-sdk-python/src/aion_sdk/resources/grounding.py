"""Grounding Manager SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class GroundingResource:
    """Client helpers for grounding and citation APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_source(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/grounding/sources", json=payload)

    def get_source(self, grounding_source_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/grounding/sources/{grounding_source_id}",
            params={"scope": list(scope)},
        )

    def create_citation(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/grounding/citations", json=payload)

    def list_citations(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if response_id:
            params["response_id"] = response_id
        if explanation_id:
            params["explanation_id"] = explanation_id
        if source_id:
            params["source_id"] = source_id
        return self._client.get("/brain/grounding/citations", params=params)

    def map_response(
        self,
        response_id: str,
        owner_scope: Sequence[str],
        required_source_types: Sequence[str] | None = None,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/grounding/map-response/{response_id}",
            json={
                "owner_scope": list(owner_scope),
                "required_source_types": list(required_source_types or []),
            },
        )

    def map_text(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/grounding/map-text", json=payload)

    def verify(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/grounding/verify", json=payload)

    def get_verification(self, grounding_verification_id: str) -> JSONValue:
        return self._client.get(f"/brain/grounding/verifications/{grounding_verification_id}")

    def coverage(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/grounding/coverage", json=payload)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/grounding/query", json=payload)

    def unsupported(
        self,
        *,
        response_id: str | None = None,
        explanation_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if response_id:
            params["response_id"] = response_id
        if explanation_id:
            params["explanation_id"] = explanation_id
        if trace_id:
            params["trace_id"] = trace_id
        return self._client.get("/brain/grounding/unsupported", params=params)


__all__ = ["GroundingResource"]
