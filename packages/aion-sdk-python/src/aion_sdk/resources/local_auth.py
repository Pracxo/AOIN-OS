"""Local auth contract SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class LocalAuthResource:
    """Client helpers for dev-only local auth APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def roles(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/local-auth/roles", params={"scope": list(scope)})

    def simulate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-auth/simulate", json=payload)

    def filter_console(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-auth/filter-console", json=payload)

    def role_matrix(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/local-auth/role-matrix", params={"scope": list(scope)})

    def role_access_audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-auth/role-access-audit", json=payload)

    def audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/local-auth/audit", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/local-auth/status", params={"scope": list(scope)})


__all__ = ["LocalAuthResource"]
