"""Approval control plane API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ApprovalsResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def inbox(
        self,
        *,
        scope: list[str] | None = None,
        status: str | None = "pending",
        priority: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        return self._client.get(
            "/brain/approvals",
            params={"scope": scope, "status": status, "priority": priority, "limit": limit},
        )

    def decide(self, approval_request_id: str, request: JSONDict) -> JSONValue:
        return self._client.post(f"/brain/approvals/{approval_request_id}/decide", json=request)

