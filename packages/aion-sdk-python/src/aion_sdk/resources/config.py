"""Runtime configuration SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConfigResource:
    """Client helpers for runtime configuration APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_profile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/runtime-config/profiles", json=payload)

    def list_profiles(
        self,
        *,
        status: str | None = None,
        profile_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if profile_type is not None:
            params["profile_type"] = profile_type
        return self._client.get("/brain/runtime-config/profiles", params=params or None)

    def activate_profile(self, config_profile_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/runtime-config/profiles/{config_profile_id}/activate",
            json={"reason": reason},
        )

    def create_feature_override(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/runtime-config/feature-overrides", json=payload)

    def list_feature_overrides(
        self,
        *,
        feature_key: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if feature_key is not None:
            params["feature_key"] = feature_key
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/runtime-config/feature-overrides", params=params or None)

    def create_snapshot(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/runtime-config/snapshots", json=payload)

    def get_snapshot(self, config_snapshot_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/runtime-config/snapshots/{config_snapshot_id}",
            params={"scope": scope},
        )

    def compare_snapshots(self, snapshot_id_a: str, snapshot_id_b: str) -> JSONValue:
        return self._client.post(
            "/brain/runtime-config/snapshots/compare",
            json={"snapshot_id_a": snapshot_id_a, "snapshot_id_b": snapshot_id_b},
        )

    def validate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/runtime-config/validate", json=payload)

    def status(self, scope: list[str]) -> JSONValue:
        return self._client.get("/brain/runtime-config/status", params={"scope": scope})
