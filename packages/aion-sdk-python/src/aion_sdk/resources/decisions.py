"""Decision intelligence SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class DecisionsResource:
    """Client helpers for decision intelligence APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_frame(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/decisions/frames", json=payload)

    def get_frame(self, decision_frame_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/decisions/frames/{decision_frame_id}",
            params={"scope": scope},
        )

    def list_frames(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        frame_type: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if status:
            params["status"] = status
        if frame_type:
            params["frame_type"] = frame_type
        return self._client.get("/brain/decisions/frames", params=params)

    def close_frame(self, decision_frame_id: str, reason: str, scope: list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/decisions/frames/{decision_frame_id}/close",
            params={"scope": scope},
            json={"reason": reason},
        )

    def create_option(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/decisions/options", json=payload)

    def list_options(self, decision_frame_id: str, status: str | None = None) -> JSONValue:
        params = {"status": status} if status else None
        return self._client.get(
            f"/brain/decisions/frames/{decision_frame_id}/options",
            params=params,
        )

    def seed_utility_profiles(self, scope: list[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/decisions/utility-profiles/seed-defaults",
            json={"scope": scope, "dry_run": dry_run},
        )

    def list_utility_profiles(
        self,
        scope: list[str],
        *,
        status: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if status:
            params["status"] = status
        return self._client.get("/brain/decisions/utility-profiles", params=params)

    def evaluate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/decisions/evaluate", json=payload)

    def recommend(self, decision_frame_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/decisions/recommend/{decision_frame_id}",
            json=payload,
        )

    def run_counterfactual(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/decisions/counterfactuals/run", json=payload)

    def get_counterfactual(self, counterfactual_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/decisions/counterfactuals/{counterfactual_run_id}")

    def record_decision(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/decisions/journal", json=payload)

    def get_decision_record(self, decision_record_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/decisions/journal/{decision_record_id}",
            params={"scope": scope},
        )

    def list_decision_records(
        self,
        scope: list[str],
        *,
        decision_frame_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if decision_frame_id:
            params["decision_frame_id"] = decision_frame_id
        if status:
            params["status"] = status
        return self._client.get("/brain/decisions/journal", params=params)
