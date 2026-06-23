"""Governed operator actions SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class OperatorActionsResource:
    """Client helpers for dry-run operator action APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_request(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("mode", "dry_run")
        return self._client.post("/brain/operator-actions/requests", json=payload)

    def get_request(self, operator_action_request_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/operator-actions/requests/{operator_action_request_id}",
            params={"scope": list(scope)},
        )

    def list_requests(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        action_type: str | None = None,
        target_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if action_type is not None:
            params["action_type"] = action_type
        if target_type is not None:
            params["target_type"] = target_type
        return self._client.get("/brain/operator-actions/requests", params=params)

    def create_preview(
        self,
        operator_action_request_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/operator-actions/requests/{operator_action_request_id}/preview",
            json={"scope": list(scope)},
        )

    def previews(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/operator-actions/previews", params=params)

    def blockers(
        self,
        scope: Sequence[str],
        *,
        operator_action_request_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if operator_action_request_id is not None:
            params["operator_action_request_id"] = operator_action_request_id
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        return self._client.get("/brain/operator-actions/blockers", params=params)

    def dismiss_blocker(
        self,
        operator_action_blocker_id: str,
        reason: str,
        actor_id: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/operator-actions/blockers/{operator_action_blocker_id}/dismiss",
            json=payload,
        )

    def review(self, operator_action_request_id: str, payload: JSONDict) -> JSONValue:
        payload["operator_action_request_id"] = operator_action_request_id
        return self._client.post(
            f"/brain/operator-actions/requests/{operator_action_request_id}/review",
            json=payload,
        )

    def reviews(
        self,
        scope: Sequence[str],
        *,
        operator_action_request_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if operator_action_request_id is not None:
            params["operator_action_request_id"] = operator_action_request_id
        if decision is not None:
            params["decision"] = decision
        return self._client.get("/brain/operator-actions/reviews", params=params)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/operator-actions/query", json=payload)


__all__ = ["OperatorActionsResource"]
