"""Operator Console SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class OperatorConsoleResource:
    """Client helpers for read-only Operator Console APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def list_views(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            "/brain/operator-console/views",
            params={"scope": list(scope)},
        )

    def view_model(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/operator-console/view-model", json=payload)

    def audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/operator-console/audit", json=payload)

    def workflows(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            "/brain/operator-console/workflows",
            params={"scope": list(scope)},
        )

    def demo_map(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            "/brain/operator-console/demo-map",
            params={"scope": list(scope)},
        )


__all__ = ["OperatorConsoleResource"]
