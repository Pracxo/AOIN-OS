"""Versioning and freeze gate SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class VersioningResource:
    """Client helpers for AION versioning and freeze gate APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_manifest(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/versioning/manifests", json=payload)

    def get_manifest(self, version: str) -> JSONValue:
        return self._client.get(f"/brain/versioning/manifests/{version}")

    def list_manifests(
        self,
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/versioning/manifests", params=params)

    def freeze_manifest(self, version: str, payload: JSONDict) -> JSONValue:
        return self._client.post(f"/brain/versioning/manifests/{version}/freeze", json=payload)

    def seed_features(self, scope: builtins.list[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/versioning/features/seed-defaults",
            json={"owner_scope": scope, "dry_run": dry_run},
        )

    def list_features(
        self,
        *,
        scope: builtins.list[str],
        status: str | None = None,
        category: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if status is not None:
            params["status"] = status
        if category is not None:
            params["category"] = category
        return self._client.get("/brain/versioning/features", params=params)

    def create_feature(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/versioning/features", json=payload)

    def deprecate_feature(
        self,
        feature_key: str,
        scope: builtins.list[str],
        reason: str,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/versioning/features/{feature_key}/deprecate",
            json={"owner_scope": scope, "reason": reason},
        )

    def generate_compatibility(self, version: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.post(
            "/brain/versioning/compatibility/generate",
            json={"version": version, "owner_scope": scope},
        )

    def get_compatibility(self, version: str) -> JSONValue:
        return self._client.get(f"/brain/versioning/compatibility/{version}")

    def generate_migration_baseline(
        self,
        version: str,
        scope: builtins.list[str],
    ) -> JSONValue:
        return self._client.post(
            "/brain/versioning/migration-baseline/generate",
            json={"schema_version": version, "owner_scope": scope},
        )

    def generate_release_artifacts(
        self,
        version: str,
        scope: builtins.list[str],
        created_by: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"version": version, "owner_scope": scope}
        if created_by is not None:
            payload["created_by"] = created_by
        return self._client.post("/brain/versioning/release-artifacts/generate", json=payload)

    def sdk_compatibility(self, scope: builtins.list[str]) -> JSONValue:
        return self._client.get("/brain/versioning/sdk-compatibility", params={"scope": scope})

    def run_freeze_gate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/freeze-gate/run", json=payload)

    def get_freeze_gate(self, freeze_gate_id: str) -> JSONValue:
        return self._client.get(f"/brain/freeze-gate/{freeze_gate_id}")

    def list_freeze_gates(
        self,
        *,
        scope: builtins.list[str],
        version: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if version is not None:
            params["version"] = version
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/freeze-gate", params=params)
