"""Instruction hierarchy and preference ledger SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class InstructionsResource:
    """Client helpers for instruction and preference APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_instruction(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/instructions", json=payload)

    def get_instruction(self, instruction_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/instructions/{instruction_id}",
            params={"scope": list(scope)},
        )

    def list_instructions(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        instruction_type: str | None = None,
        scope_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status:
            params["status"] = status
        if instruction_type:
            params["instruction_type"] = instruction_type
        if scope_type:
            params["scope_type"] = scope_type
        return self._client.get("/brain/instructions", params=params)

    def disable_instruction(self, instruction_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/instructions/{instruction_id}/disable",
            json={"reason": reason},
        )

    def resolve(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/instructions/resolve", json=payload)

    def list_conflicts(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        return self._client.get("/brain/instructions/conflicts", params=params)

    def resolve_conflict(self, conflict_id: str, resolution: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/instructions/conflicts/{conflict_id}/resolve",
            json={"resolution": resolution, "reason": reason},
        )

    def create_preference(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/preferences", json=payload)

    def list_preferences(
        self,
        scope: Sequence[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        preference_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if actor_id:
            params["actor_id"] = actor_id
        if workspace_id:
            params["workspace_id"] = workspace_id
        if status:
            params["status"] = status
        if preference_type:
            params["preference_type"] = preference_type
        return self._client.get("/brain/preferences", params=params)

    def confirm_preference(self, preference_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/preferences/{preference_id}/confirm",
            json={"reason": reason},
        )

    def reject_preference(self, preference_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/preferences/{preference_id}/reject",
            json={"reason": reason},
        )

    def list_candidates(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        preference_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status:
            params["status"] = status
        if preference_type:
            params["preference_type"] = preference_type
        return self._client.get("/brain/preferences/candidates", params=params)

    def confirm_candidate(self, candidate_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/preferences/candidates/{candidate_id}/confirm",
            json={"reason": reason},
        )

    def reject_candidate(self, candidate_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/preferences/candidates/{candidate_id}/reject",
            json={"reason": reason},
        )

    def create_style_profile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/style-profiles", json=payload)

    def list_style_profiles(
        self,
        scope: Sequence[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if actor_id:
            params["actor_id"] = actor_id
        if workspace_id:
            params["workspace_id"] = workspace_id
        if status:
            params["status"] = status
        return self._client.get("/brain/style-profiles", params=params)

    def effective_style(
        self,
        scope: Sequence[str],
        *,
        actor_id: str | None = None,
        workspace_id: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope)}
        if actor_id:
            params["actor_id"] = actor_id
        if workspace_id:
            params["workspace_id"] = workspace_id
        return self._client.get("/brain/style-profiles/effective", params=params)


__all__ = ["InstructionsResource"]
