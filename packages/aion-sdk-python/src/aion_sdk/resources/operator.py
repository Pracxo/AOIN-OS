"""Operator Control Tower SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class OperatorResource:
    """Client helpers for Operator Control Tower APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def overview(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/operator/overview", json=payload)

    def status_cards(self, scope: list[str]) -> JSONValue:
        return self._client.get("/brain/operator/status-cards", params={"scope": scope})

    def queues(self, scope: list[str]) -> JSONValue:
        return self._client.get("/brain/operator/queues", params={"scope": scope})

    def actions(self, scope: list[str], limit: int = 100) -> JSONValue:
        return self._client.get(
            "/brain/operator/actions",
            params={"scope": scope, "limit": limit},
        )

    def acknowledge(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/operator/actions/acknowledge", json=payload)

    def readiness(self, scope: list[str]) -> JSONValue:
        return self._client.get("/brain/operator/readiness", params={"scope": scope})

    def create_snapshot(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/operator/snapshots", json=payload)

    def get_snapshot(self, operator_snapshot_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/operator/snapshots/{operator_snapshot_id}",
            params={"scope": scope},
        )

    def list_snapshots(
        self,
        scope: list[str],
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if snapshot_type is not None:
            params["snapshot_type"] = snapshot_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/operator/snapshots", params=params)

    def runbooks(self, category: str | None = None) -> JSONValue:
        params = {"category": category} if category is not None else None
        return self._client.get("/brain/operator/runbooks", params=params)
