"""Performance SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class PerformanceResource:
    """Client helpers for local performance benchmark APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_benchmark(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/performance/benchmarks", json=payload)

    def list_benchmarks(
        self,
        *,
        status: str | None = None,
        benchmark_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if benchmark_type is not None:
            params["benchmark_type"] = benchmark_type
        return self._client.get("/brain/performance/benchmarks", params=params or None)

    def seed_defaults(self, scope: builtins.list[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/performance/benchmarks/seed-defaults",
            json={"scope": scope, "dry_run": dry_run},
        )

    def run_benchmark(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/performance/benchmarks/run", json=payload)

    def get_run(self, benchmark_run_id: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/performance/benchmarks/runs/{benchmark_run_id}",
            params={"scope": scope},
        )

    def create_baseline(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/performance/baselines/from-runs", json=payload)

    def list_baselines(
        self,
        *,
        version: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if version is not None:
            params["version"] = version
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/performance/baselines", params=params or None)

    def compare_regression(self, benchmark_run_id: str, baseline_id: str) -> JSONValue:
        return self._client.post(
            "/brain/performance/regression/compare",
            json={"benchmark_run_id": benchmark_run_id, "baseline_id": baseline_id},
        )

    def summary(
        self,
        scope: builtins.list[str],
        *,
        operation_type: str | None = None,
        window: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if operation_type is not None:
            params["operation_type"] = operation_type
        if window is not None:
            params["window"] = window
        return self._client.get("/brain/performance/summary", params=params)
