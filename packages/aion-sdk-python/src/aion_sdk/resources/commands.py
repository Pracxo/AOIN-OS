"""Command Bus API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class CommandsResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def dispatch(self, request: JSONDict, *, idempotency_key: str | None = None) -> JSONValue:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._client.post("/brain/commands", json=request, headers=headers)

    def get(self, command_id: str) -> JSONValue:
        return self._client.get(f"/brain/commands/{command_id}")

    def list(
        self,
        *,
        status: str | None = None,
        command_type: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        return self._client.get(
            "/brain/commands",
            params={
                "status": status,
                "command_type": command_type,
                "trace_id": trace_id,
                "limit": limit,
            },
        )

