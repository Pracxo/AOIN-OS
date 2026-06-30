"""Connector sandbox SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConnectorSandboxResource:
    """Client helpers for connector sandbox design and readiness preview APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def boundary(self) -> JSONValue:
        return self._client.get("/brain/connector-sandbox/boundary")

    def capability_rules(self) -> JSONValue:
        return self._client.get("/brain/connector-sandbox/capability-rules")

    def readiness(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-sandbox/readiness", json=payload)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-sandbox/query", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/connector-sandbox/status", params={"scope": list(scope)})


__all__ = ["ConnectorSandboxResource"]
