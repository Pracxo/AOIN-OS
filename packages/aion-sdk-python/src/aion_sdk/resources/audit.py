"""Audit integrity SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class AuditResource:
    """Client helpers for audit integrity and provenance APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def record(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/audit/entries", json=payload)

    def get_entry(self, audit_entry_id: str) -> JSONValue:
        return self._client.get(f"/brain/audit/entries/{audit_entry_id}")

    def get_by_sequence(self, sequence_number: int) -> JSONValue:
        return self._client.get(f"/brain/audit/entries/by-sequence/{sequence_number}")

    def list_entries(
        self,
        *,
        trace_id: str | None = None,
        resource_type: str | None = None,
        action_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if trace_id is not None:
            params["trace_id"] = trace_id
        if resource_type is not None:
            params["resource_type"] = resource_type
        if action_type is not None:
            params["action_type"] = action_type
        return self._client.get("/brain/audit/entries", params=params)

    def status(self) -> JSONValue:
        return self._client.get("/brain/audit/status")

    def create_checkpoint(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/audit/checkpoints", json=payload)

    def list_checkpoints(self, limit: int = 50) -> JSONValue:
        return self._client.get("/brain/audit/checkpoints", params={"limit": limit})

    def verify(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/audit/verify", json=payload)

    def export(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/audit/export", json=payload)

    def create_provenance_link(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/provenance/links", json=payload)

    def list_provenance_links(
        self,
        *,
        source_type: str | None = None,
        source_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if source_type is not None:
            params["source_type"] = source_type
        if source_id is not None:
            params["source_id"] = source_id
        if target_type is not None:
            params["target_type"] = target_type
        if target_id is not None:
            params["target_id"] = target_id
        if trace_id is not None:
            params["trace_id"] = trace_id
        return self._client.get("/brain/provenance/links", params=params)

    def trace_provenance(self, trace_id: str, limit: int = 500) -> JSONValue:
        return self._client.get(
            f"/brain/provenance/traces/{trace_id}",
            params={"limit": limit},
        )
