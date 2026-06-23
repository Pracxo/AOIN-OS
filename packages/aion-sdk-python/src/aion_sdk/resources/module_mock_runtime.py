"""Module mock runtime SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ModuleMockRuntimeResource:
    """Client helpers for deterministic module mock runtime APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_profile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-mock/profiles", json=payload)

    def seed_profiles(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-mock/profiles/seed-defaults", json=payload)

    def list_profiles(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "profile_type", profile_type)
        return self._client.get("/brain/module-mock/profiles", params=params)

    def get_profile(self, mock_profile_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-mock/profiles/{mock_profile_id}",
            params={"scope": list(scope)},
        )

    def invoke(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-mock/invoke", json=payload)

    def list_runs(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "capability_binding_id", capability_binding_id)
        return self._client.get("/brain/module-mock/runs", params=params)

    def get_run(self, module_mock_run_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-mock/runs/{module_mock_run_id}",
            params={"scope": list(scope)},
        )

    def outputs(
        self,
        scope: Sequence[str],
        *,
        module_mock_run_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "module_mock_run_id", module_mock_run_id)
        _set(params, "capability_binding_id", capability_binding_id)
        _set(params, "status", status)
        return self._client.get("/brain/module-mock/outputs", params=params)

    def get_output(self, module_mock_output_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-mock/outputs/{module_mock_output_id}",
            params={"scope": list(scope)},
        )

    def list_findings(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "severity", severity)
        _set(params, "capability_binding_id", capability_binding_id)
        return self._client.get("/brain/module-mock/findings", params=params)

    def dismiss_finding(self, module_mock_finding_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/module-mock/findings/{module_mock_finding_id}/dismiss",
            json=payload,
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-mock/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["ModuleMockRuntimeResource"]
