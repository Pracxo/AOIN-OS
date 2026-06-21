"""Action proposal broker SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ActionProposalsResource:
    """Client helpers for action proposal broker APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/action-proposals", json=payload)

    def get(self, action_proposal_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/action-proposals/{action_proposal_id}",
            params={"scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/action-proposals/query", json=payload)

    def archive(
        self,
        action_proposal_id: str,
        reason: str,
        actor_id: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/action-proposals/{action_proposal_id}/archive",
            json=payload,
        )

    def delete(
        self,
        action_proposal_id: str,
        reason: str,
        actor_id: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.delete(f"/brain/action-proposals/{action_proposal_id}", json=payload)

    def review_tool_intent(self, tool_intent_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/action-proposals/tool-intents/{tool_intent_id}/review",
            json=payload,
        )

    def list_tool_intent_reviews(
        self,
        *,
        tool_intent_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if tool_intent_id is not None:
            params["tool_intent_id"] = tool_intent_id
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/action-proposals/tool-intent-reviews", params=params)

    def review(self, action_proposal_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/action-proposals/{action_proposal_id}/review",
            json=payload,
        )

    def list_reviews(self, action_proposal_id: str) -> JSONValue:
        return self._client.get(f"/brain/action-proposals/{action_proposal_id}/reviews")

    def list_blockers(
        self,
        *,
        action_proposal_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if action_proposal_id is not None:
            params["action_proposal_id"] = action_proposal_id
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        return self._client.get("/brain/action-proposals/blockers", params=params)

    def resolve_blocker(
        self,
        action_blocker_id: str,
        reason: str,
        actor_id: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/action-proposals/blockers/{action_blocker_id}/resolve",
            json=payload,
        )

    def handoff(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("mode", "dry_run")
        return self._client.post("/brain/action-proposals/handoff", json=payload)

    def get_handoff(self, execution_handoff_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/action-proposals/handoffs/{execution_handoff_id}",
            params={"scope": list(scope)},
        )

    def list_handoffs(
        self,
        *,
        action_proposal_id: str | None = None,
        status: str | None = None,
        target_system: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if action_proposal_id is not None:
            params["action_proposal_id"] = action_proposal_id
        if status is not None:
            params["status"] = status
        if target_system is not None:
            params["target_system"] = target_system
        return self._client.get("/brain/action-proposals/handoffs", params=params)


__all__ = ["ActionProposalsResource"]
