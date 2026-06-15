"""Visual Brain Projection API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class VisualResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def map(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/visual/map", json=request)

    def recent(self, *, scope: list[str], limit: int = 100) -> JSONValue:
        return self._client.get(
            "/brain/visual/telemetry/recent",
            params={"scope": scope, "limit": limit},
        )

    def timeline(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/visual/timeline", json=request)

