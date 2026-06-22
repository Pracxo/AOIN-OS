"""First-run bootstrap SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class BootstrapResource:
    """Client helpers for local first-run bootstrap APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def seed_profiles(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> JSONValue:
        return self._client.post(
            "/brain/bootstrap/profiles/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run, "created_by": created_by},
        )

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
        return self._client.get("/brain/bootstrap/profiles", params=params)

    def seed_bundles(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> JSONValue:
        return self._client.post(
            "/brain/bootstrap/seed-bundles/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run, "created_by": created_by},
        )

    def list_seed_bundles(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        bundle_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "bundle_type", bundle_type)
        return self._client.get("/brain/bootstrap/seed-bundles", params=params)

    def seed(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/bootstrap/seed", json=payload)

    def doctor(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/bootstrap/doctor", json=payload)

    def run(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/bootstrap/run", json=payload)

    def list_runs(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        profile_key: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "profile_key", profile_key)
        return self._client.get("/brain/bootstrap/runs", params=params)

    def get_run(self, bootstrap_run_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/bootstrap/runs/{bootstrap_run_id}",
            params={"scope": list(scope)},
        )

    def list_findings(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        category: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "severity", severity)
        _set(params, "category", category)
        return self._client.get("/brain/bootstrap/findings", params=params)

    def dismiss_finding(
        self,
        setup_finding_id: str,
        scope: Sequence[str],
        *,
        reason: str = "dismissed",
    ) -> JSONValue:
        return self._client.post(
            f"/brain/bootstrap/findings/{setup_finding_id}/dismiss",
            params={"scope": list(scope)},
            json={"reason": reason},
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
        return self._client.get("/brain/bootstrap/reports", params=params)

    def get_report(self, setup_report_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/bootstrap/reports/{setup_report_id}",
            params={"scope": list(scope)},
        )


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["BootstrapResource"]
