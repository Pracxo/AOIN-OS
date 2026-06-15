"""Scenario harness SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ScenariosResource:
    """Client helpers for scenario and release baseline APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/scenarios", json=payload)

    def list(
        self,
        *,
        status: str | None = None,
        scenario_type: str | None = None,
        tags: builtins.list[str] | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if scenario_type is not None:
            params["scenario_type"] = scenario_type
        if tags:
            params["tags"] = tags
        return self._client.get("/brain/scenarios", params=params)

    def get(self, scenario_id: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/scenarios/{scenario_id}",
            params={"scope": scope},
        )

    def run(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/scenarios/run", json=payload)

    def get_run(self, scenario_run_id: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/scenarios/runs/{scenario_run_id}",
            params={"scope": scope},
        )

    def runs(
        self,
        *,
        scope: builtins.list[str],
        status: str | None = None,
        scenario_type: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if status is not None:
            params["status"] = status
        if scenario_type is not None:
            params["scenario_type"] = scenario_type
        return self._client.get("/brain/scenarios/runs", params=params)

    def seed_defaults(self, scope: builtins.list[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/scenarios/seed-defaults",
            json={"scope": scope, "dry_run": dry_run},
        )

    def list_fixtures(
        self,
        scope: builtins.list[str],
        fixture_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if fixture_type is not None:
            params["fixture_type"] = fixture_type
        return self._client.get("/brain/demo-fixtures", params=params)

    def load_fixture(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/demo-fixtures/load", json=payload)

    def run_release_baseline(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/release-baseline/run", json=payload)

    def get_release_baseline(self, release_baseline_id: str) -> JSONValue:
        return self._client.get(f"/brain/release-baseline/{release_baseline_id}")

    def list_release_baselines(
        self,
        *,
        scope: builtins.list[str],
        version: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if version is not None:
            params["version"] = version
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/release-baseline", params=params)
