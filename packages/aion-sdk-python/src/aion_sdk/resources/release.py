"""Release package SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ReleaseResource:
    """Client helpers for local release package APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_package(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/release-package/create", json=payload)

    def get_package(
        self,
        release_package_id: str,
        scope: builtins.list[str] | None = None,
    ) -> JSONValue:
        params = {"scope": scope} if scope else None
        return self._client.get(f"/brain/release-package/{release_package_id}", params=params)

    def list_packages(
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
        return self._client.get("/brain/release-package", params=params)

    def validate_package(
        self,
        release_package_id: str,
        scope: builtins.list[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/release-package/{release_package_id}/validate",
            params={"scope": scope},
        )

    def handoff(
        self,
        release_package_id: str,
        scope: builtins.list[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/release-package/{release_package_id}/handoff",
            params={"scope": scope},
        )
