"""Reasoning API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ReasoningResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def reason(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/reason", json=request)

    def get_reasoning(self, reasoning_id: str) -> JSONValue:
        return self._client.get(f"/brain/reason/{reasoning_id}")
