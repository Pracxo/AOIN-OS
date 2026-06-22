"""Situation model SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class SituationsResource:
    """Client helpers for situation model APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/situations", json=payload)

    def get(self, situation_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(f"/brain/situations/{situation_id}", params={"scope": scope})

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/situations/query", json=payload)

    def close(self, situation_id: str, reason: str, scope: list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/situations/{situation_id}/close",
            params={"scope": scope},
            json={"reason": reason},
        )

    def create_atom(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/situations/state-atoms", json=payload)

    def get_atom(self, state_atom_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/situations/state-atoms/{state_atom_id}",
            params={"scope": scope},
        )

    def list_atoms(
        self,
        scope: list[str],
        *,
        situation_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if situation_id:
            params["situation_id"] = situation_id
        if trace_id:
            params["trace_id"] = trace_id
        return self._client.get("/brain/situations/state-atoms", params=params)

    def project(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/situations/project", json=payload)

    def get_projection_run(self, projection_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/situations/projection-runs/{projection_run_id}")

    def list_transitions(
        self,
        *,
        trace_id: str | None = None,
        situation_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        if situation_id:
            params["situation_id"] = situation_id
        return self._client.get("/brain/situations/transitions", params=params)

    def create_temporal_window(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/situations/temporal-windows", json=payload)

    def get_temporal_window(self, temporal_window_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/situations/temporal-windows/{temporal_window_id}",
            params={"scope": scope},
        )

    def list_temporal_windows(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        return self._client.get("/brain/situations/temporal-windows", params=params)

    def record_continuity(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/situations/continuity", json=payload)

    def list_continuity(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        situation_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        if situation_id:
            params["situation_id"] = situation_id
        return self._client.get("/brain/situations/continuity", params=params)
