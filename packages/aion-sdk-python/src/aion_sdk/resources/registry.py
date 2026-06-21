"""Global Resource Registry SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class RegistryResource:
    """Client helpers for resource registry and link integrity APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def upsert_resource(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/registry/resources", json=payload)

    def get_resource(
        self,
        resource_type: str,
        resource_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/registry/resources/{resource_type}/{resource_id}",
            params={"scope": list(scope)},
        )

    def get_by_uri(self, resource_uri: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            "/brain/registry/resources/by-uri",
            params={"resource_uri": resource_uri, "scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/registry/query", json=payload)

    def create_link(self, payload: JSONDict, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            "/brain/registry/links",
            json=payload,
            params={"scope": list(scope)},
        )

    def list_links(
        self,
        scope: Sequence[str],
        *,
        source_uri: str | None = None,
        target_uri: str | None = None,
        relation_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if source_uri is not None:
            params["source_uri"] = source_uri
        if target_uri is not None:
            params["target_uri"] = target_uri
        if relation_type is not None:
            params["relation_type"] = relation_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/registry/links", params=params)

    def list_backlinks(
        self,
        resource_uri: str,
        scope: Sequence[str],
        *,
        limit: int = 100,
    ) -> JSONValue:
        return self._client.get(
            "/brain/registry/backlinks",
            params={"resource_uri": resource_uri, "scope": list(scope), "limit": limit},
        )

    def validate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/registry/validate", json=payload)

    def get_validation_run(self, validation_run_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/registry/validation-runs/{validation_run_id}",
            params={"scope": list(scope)},
        )

    def list_broken_references(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        validation_run_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self._integrity_list(
            "/brain/registry/broken-references",
            scope,
            status=status,
            severity=severity,
            validation_run_id=validation_run_id,
            limit=limit,
        )

    def dismiss_broken_reference(
        self,
        broken_reference_id: str,
        reason: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/registry/broken-references/{broken_reference_id}/dismiss",
            json={"reason": reason},
            params={"scope": list(scope)},
        )

    def list_orphaned_resources(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        validation_run_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self._integrity_list(
            "/brain/registry/orphaned-resources",
            scope,
            status=status,
            severity=severity,
            validation_run_id=validation_run_id,
            limit=limit,
        )

    def dismiss_orphaned_resource(
        self,
        orphaned_resource_id: str,
        reason: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/registry/orphaned-resources/{orphaned_resource_id}/dismiss",
            json={"reason": reason},
            params={"scope": list(scope)},
        )

    def rebuild(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/registry/rebuild", json=payload)

    def get_rebuild_run(self, rebuild_run_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/registry/rebuild-runs/{rebuild_run_id}",
            params={"scope": list(scope)},
        )

    def create_snapshot(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/registry/snapshots", json=payload)

    def get_snapshot(self, registry_snapshot_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/registry/snapshots/{registry_snapshot_id}",
            params={"scope": list(scope)},
        )

    def list_snapshots(
        self,
        scope: Sequence[str],
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if snapshot_type is not None:
            params["snapshot_type"] = snapshot_type
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/registry/snapshots", params=params)

    def _integrity_list(
        self,
        path: str,
        scope: Sequence[str],
        *,
        status: str | None,
        severity: str | None,
        validation_run_id: str | None,
        limit: int,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        if validation_run_id is not None:
            params["validation_run_id"] = validation_run_id
        return self._client.get(path, params=params)


__all__ = ["RegistryResource"]
