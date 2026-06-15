"""Autonomy Governor API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class AutonomyResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def status(
        self,
        *,
        scope: list[str] | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> JSONValue:
        return self._client.get(
            "/brain/autonomy/status",
            params={"scope": scope, "actor_id": actor_id, "workspace_id": workspace_id},
        )

    def decide(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/autonomy/decide", json=request)

    def set_run_level(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/autonomy/run-levels", json=request)

