"""Disabled connector runtime SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConnectorRuntimeResource:
    """Client helpers for disabled external connector runtime APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/connector-runtime/status", params={"scope": list(scope)})

    def validate_manifest(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-runtime/mock-manifest/validate", json=payload)

    def egress_preview(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("preview_type", "dry_run")
        return self._client.post("/brain/connector-runtime/egress-preview", json=payload)

    def ingress_preview(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("preview_type", "dry_run")
        return self._client.post("/brain/connector-runtime/ingress-preview", json=payload)

    def audit(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-runtime/audit", json=payload)


__all__ = ["ConnectorRuntimeResource"]
