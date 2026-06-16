"""Response SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ResponsesResource:
    """Client helpers for deterministic response APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def compose(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/responses/compose", json=payload)

    def get(self, response_id: str) -> JSONValue:
        return self._client.get(f"/brain/responses/{response_id}")

    def verify(self, response_id: str) -> JSONValue:
        return self._client.post(f"/brain/responses/{response_id}/verify")

    def deliver_local(self, response_id: str) -> JSONValue:
        return self._client.post(f"/brain/responses/{response_id}/deliver-local")

    def deliveries(self, response_id: str) -> JSONValue:
        return self._client.get(f"/brain/responses/{response_id}/deliveries")
