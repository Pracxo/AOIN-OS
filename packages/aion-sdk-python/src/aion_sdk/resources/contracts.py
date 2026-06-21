"""Contract Registry SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ContractsResource:
    """Client helpers for Contract Registry APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def list_contracts(
        self,
        scope: Sequence[str],
        contract_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if contract_type is not None:
            params["contract_type"] = contract_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/contracts/contracts", params=params)

    def list_interfaces(
        self,
        scope: Sequence[str],
        interface_type: str | None = None,
        source_system: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if interface_type is not None:
            params["interface_type"] = interface_type
        if source_system is not None:
            params["source_system"] = source_system
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/contracts/interfaces", params=params)

    def create_snapshot(
        self,
        scope: Sequence[str],
        snapshot_type: str = "manual",
        trace_id: str | None = None,
    ) -> JSONValue:
        return self._client.post(
            "/brain/contracts/snapshots",
            json={"scope": list(scope), "snapshot_type": snapshot_type, "trace_id": trace_id},
        )

    def get_snapshot(self, contract_snapshot_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/contracts/snapshots/{contract_snapshot_id}",
            params={"scope": list(scope)},
        )

    def list_snapshots(
        self,
        scope: Sequence[str],
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if snapshot_type is not None:
            params["snapshot_type"] = snapshot_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/contracts/snapshots", params=params)

    def create_rule(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/contracts/rules", json=payload)

    def list_rules(
        self,
        scope: Sequence[str],
        status: str | None = None,
        rule_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if rule_type is not None:
            params["rule_type"] = rule_type
        return self._client.get("/brain/contracts/rules", params=params)

    def seed_rules(self, scope: Sequence[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/contracts/rules/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run},
        )

    def scan_compatibility(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/contracts/compatibility/scan", json=payload)

    def get_scan(self, compatibility_scan_id: str) -> JSONValue:
        return self._client.get(f"/brain/contracts/compatibility/scans/{compatibility_scan_id}")

    def findings(
        self,
        status: str | None = None,
        severity: str | None = None,
        breaking: bool | None = None,
        interface_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        if breaking is not None:
            params["breaking"] = breaking
        if interface_type is not None:
            params["interface_type"] = interface_type
        return self._client.get("/brain/contracts/findings", params=params)

    def dismiss_finding(self, drift_finding_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/contracts/findings/{drift_finding_id}/dismiss",
            json={"reason": reason},
        )

    def migration_notes(
        self,
        scope: Sequence[str],
        status: str | None = None,
        note_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if note_type is not None:
            params["note_type"] = note_type
        return self._client.get("/brain/contracts/migration-notes", params=params)

    def report(self, scope: Sequence[str], trace_id: str | None = None) -> JSONValue:
        return self._client.post(
            "/brain/contracts/report",
            json={"scope": list(scope), "trace_id": trace_id},
        )


__all__ = ["ContractsResource"]
