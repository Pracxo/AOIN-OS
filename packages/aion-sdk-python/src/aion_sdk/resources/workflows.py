"""Workflow API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class WorkflowsResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/workflows", json=request)

    def run(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/workflows/run", json=request)

    def get_run(self, workflow_run_id: str, *, scope: list[str] | None = None) -> JSONValue:
        return self._client.get(
            f"/brain/workflows/runs/{workflow_run_id}",
            params={"scope": scope} if scope else None,
        )

    def status(self) -> JSONValue:
        return self._client.get("/brain/workflows/engine/status")

