"""Golden Path Scenario Harness SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class GoldenPathResource:
    """Client helpers for golden path scenario harness APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_scenario(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/golden-path/scenarios", json=payload)

    def get_scenario(self, scenario_key: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/golden-path/scenarios/{scenario_key}",
            params={"scope": list(scope)},
        )

    def list_scenarios(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        scenario_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "scenario_type", scenario_type)
        return self._client.get("/brain/golden-path/scenarios", params=params)

    def seed_default_scenarios(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
    ) -> JSONValue:
        return self._client.post(
            "/brain/golden-path/scenarios/seed-defaults",
            params={"scope": list(scope), "dry_run": dry_run},
        )

    def seed_default_fixtures(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
    ) -> JSONValue:
        return self._client.post(
            "/brain/golden-path/fixtures/seed-defaults",
            params={"scope": list(scope), "dry_run": dry_run},
        )

    def list_fixtures(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        return self._client.get("/brain/golden-path/fixtures", params=params)

    def run(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/golden-path/run", json=payload)

    def get_run(self, golden_path_run_id: str, scope: Sequence[str] | None = None) -> JSONValue:
        params = {"scope": list(scope)} if scope is not None else None
        return self._client.get(
            f"/brain/golden-path/runs/{golden_path_run_id}",
            params=params,
        )

    def list_runs(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "trace_id", trace_id)
        return self._client.get("/brain/golden-path/runs", params=params)

    def release_smoke(self, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            "/brain/golden-path/release-smoke",
            params={"scope": list(scope)},
        )

    def get_report(self, golden_path_report_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/golden-path/reports/{golden_path_report_id}",
            params={"scope": list(scope)},
        )

    def list_reports(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        return self._client.get("/brain/golden-path/reports", params=params)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/golden-path/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["GoldenPathResource"]
