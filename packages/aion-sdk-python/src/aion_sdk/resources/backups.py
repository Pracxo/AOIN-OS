"""Backup and restore SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class BackupsResource:
    """Client helpers for local backup and restore-preview APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def export(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/backups/export", json=payload)

    def get(self, backup_job_id: str, scope: builtins.list[str] | None = None) -> JSONValue:
        params = {"scope": scope} if scope else None
        return self._client.get(f"/brain/backups/{backup_job_id}", params=params)

    def list(
        self,
        *,
        scope: builtins.list[str],
        workspace_id: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/backups", params=params)

    def validate(self, backup_job_id: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/backups/{backup_job_id}/validate",
            params={"scope": scope},
        )

    def validate_path(self, backup_path: str, scope: builtins.list[str]) -> JSONValue:
        return self._client.post(
            "/brain/backups/validate-path",
            json={"backup_path": backup_path, "scope": scope},
        )

    def restore_preview(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/restore/preview", json=payload)

    def get_restore_preview(
        self,
        restore_preview_id: str,
        scope: builtins.list[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/restore/previews/{restore_preview_id}",
            params={"scope": scope},
        )

    def restore_apply(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/restore/apply", json=payload)
