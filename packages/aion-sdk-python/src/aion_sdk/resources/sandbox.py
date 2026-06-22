"""Sandbox Control Plane API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class SandboxResource:
    """Public sandbox, secret reference, and connector API wrapper."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_profile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/sandbox/profiles", json=payload)

    def list_profiles(self, scope: list[str], status: str | None = None) -> JSONValue:
        return self._client.get(
            "/brain/sandbox/profiles",
            params={"scope": scope, "status": status},
        )

    def validate_profile(self, sandbox_profile_id: str, scope: list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/sandbox/profiles/{sandbox_profile_id}/validate",
            json={"scope": scope},
        )

    def run(self, payload: JSONDict) -> JSONValue:
        request = {"mode": "dry_run", **payload}
        return self._client.post("/brain/sandbox/run", json=request)

    def create_secret_ref(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/secret-refs", json=payload)

    def list_secret_refs(self, scope: list[str], status: str | None = None) -> JSONValue:
        return self._client.get(
            "/brain/secret-refs",
            params={"scope": scope, "status": status},
        )

    def create_connector(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connectors", json=payload)

    def list_connectors(
        self,
        scope: list[str],
        status: str | None = None,
        connector_type: str | None = None,
    ) -> JSONValue:
        return self._client.get(
            "/brain/connectors",
            params={"scope": scope, "status": status, "connector_type": connector_type},
        )

    def validate_connector(self, connector_id: str, scope: list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/connectors/{connector_id}/validate",
            json={"scope": scope},
        )
