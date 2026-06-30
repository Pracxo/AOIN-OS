"""Connector policy SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConnectorPolicyResource:
    """Client helpers for connector policy catalog and dry-run APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def catalog(self) -> JSONValue:
        return self._client.get("/brain/connector-policy/catalog")

    def matrix(self) -> JSONValue:
        return self._client.get("/brain/connector-policy/matrix")

    def dry_run(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-policy/dry-run", json=payload)

    def query_traceability(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-policy/traceability/query", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/connector-policy/status", params={"scope": list(scope)})


__all__ = ["ConnectorPolicyResource"]
