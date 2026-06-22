"""Dialogue SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class DialogueResource:
    """Client helpers for dialogue APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_session(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/dialogue/sessions", json=payload)

    def get_session(self, dialogue_session_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/dialogue/sessions/{dialogue_session_id}",
            params={"scope": scope},
        )

    def list_sessions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        session_type: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if status is not None:
            params["status"] = status
        if session_type is not None:
            params["session_type"] = session_type
        return self._client.get("/brain/dialogue/sessions", params=params)

    def close_session(self, dialogue_session_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/dialogue/sessions/{dialogue_session_id}/close",
            json={"reason": reason},
        )

    def create_message(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/dialogue/messages", json=payload)

    def list_messages(
        self,
        dialogue_session_id: str,
        scope: list[str],
        limit: int = 100,
    ) -> JSONValue:
        return self._client.get(
            f"/brain/dialogue/sessions/{dialogue_session_id}/messages",
            params={"scope": scope, "limit": limit},
        )

    def turn(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/dialogue/turn", json=payload)

    def pending_clarifications(
        self,
        scope: list[str],
        dialogue_session_id: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if dialogue_session_id is not None:
            params["dialogue_session_id"] = dialogue_session_id
        return self._client.get("/brain/dialogue/clarifications/pending", params=params)

    def answer_clarification(self, clarification_id: str, answer: str) -> JSONValue:
        return self._client.post(
            f"/brain/dialogue/clarifications/{clarification_id}/answer",
            json={"clarification_id": clarification_id, "answer": answer},
        )

    def feedback(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/dialogue/feedback", json=payload)
