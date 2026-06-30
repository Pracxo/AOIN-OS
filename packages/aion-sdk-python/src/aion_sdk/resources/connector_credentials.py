"""Connector credentials SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConnectorCredentialsResource:
    """Client helpers for connector credential architecture preview APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def boundary(self) -> JSONValue:
        return self._client.get("/brain/connector-credentials/boundary")

    def lifecycle(self) -> JSONValue:
        return self._client.get("/brain/connector-credentials/lifecycle")

    def authorization(self) -> JSONValue:
        return self._client.get("/brain/connector-credentials/authorization")

    def readiness(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-credentials/readiness", json=payload)

    def redaction_preview(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-credentials/redaction-preview", json=payload)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-credentials/query", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            "/brain/connector-credentials/status",
            params={"scope": list(scope)},
        )


__all__ = ["ConnectorCredentialsResource"]
