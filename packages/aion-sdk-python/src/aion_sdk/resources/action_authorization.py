"""Dry-run action authorization SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ActionAuthorizationResource:
    """Client helpers for dry-run action authorization APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def authorize(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("mode", "dry_run")
        return self._client.post("/brain/action-authorization/authorize", json=payload)

    def audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/action-authorization/audit", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            "/brain/action-authorization/status",
            params={"scope": list(scope)},
        )


__all__ = ["ActionAuthorizationResource"]
