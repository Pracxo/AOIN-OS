"""Disabled auth runtime SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class AuthRuntimeResource:
    """Client helpers for disabled production auth runtime APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/auth-runtime/status", params={"scope": list(scope)})

    def mock_claims_preview(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("mode", "preview")
        return self._client.post("/brain/auth-runtime/mock-claims/preview", json=payload)

    def audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/auth-runtime/audit", json=payload)


__all__ = ["AuthRuntimeResource"]
