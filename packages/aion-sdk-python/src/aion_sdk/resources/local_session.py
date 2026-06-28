"""Local session prototype SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class LocalSessionResource:
    """Client helpers for read-only local session prototype APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def preview(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-session/preview", json=payload)

    def context(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-session/context", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/local-session/status", params={"scope": list(scope)})

    def boundary_check(self, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            "/brain/local-session/boundary-check",
            json={"scope": list(scope)},
        )

    def audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-session/audit", json=payload)


__all__ = ["LocalSessionResource"]
