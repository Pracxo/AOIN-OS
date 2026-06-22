"""Security baseline SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class SecurityResource:
    """Client helpers for local security baseline APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def run_scan(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/security/scans/run", json=payload)

    def get_scan(self, security_scan_id: str) -> JSONValue:
        return self._client.get(f"/brain/security/scans/{security_scan_id}")

    def list_scans(
        self,
        *,
        scan_type: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if scan_type is not None:
            params["scan_type"] = scan_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/security/scans", params=params or None)

    def seed_threat_models(
        self,
        owner_scope: builtins.list[str],
        dry_run: bool = True,
    ) -> JSONValue:
        return self._client.post(
            "/brain/security/threat-models/seed-defaults",
            json={"owner_scope": owner_scope, "dry_run": dry_run},
        )

    def list_threat_models(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        return self._client.get("/brain/security/threat-models", params=params or None)

    def seed_controls(self, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/security/controls/seed-defaults",
            json={"dry_run": dry_run},
        )

    def list_controls(
        self,
        *,
        status: str | None = None,
        category: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        return self._client.get("/brain/security/controls", params=params or None)

    def run_hardening_gate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/security/hardening-gate/run", json=payload)

    def get_hardening_gate(self, hardening_gate_id: str) -> JSONValue:
        return self._client.get(f"/brain/security/hardening-gate/{hardening_gate_id}")
