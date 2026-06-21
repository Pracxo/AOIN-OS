"""Extension Registry SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ExtensionsResource:
    """Client helpers for metadata-only Extension Registry APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def validate_manifest(self, manifest: JSONDict) -> JSONValue:
        return self._client.post("/brain/extensions/manifests/validate", json=manifest)

    def intake(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/extensions/intake", json=payload)

    def get_intake_run(
        self,
        extension_intake_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/extensions/intake-runs/{extension_intake_id}",
            params={"scope": list(scope)},
        )

    def get_package(self, extension_package_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/extensions/packages/{extension_package_id}",
            params={"scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/extensions/query", json=payload)

    def archive_package(
        self,
        extension_package_id: str,
        payload: JSONDict,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/extensions/packages/{extension_package_id}/archive",
            json=payload,
            params={"scope": list(scope)},
        )

    def delete_package(self, extension_package_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.delete(
            f"/brain/extensions/packages/{extension_package_id}",
            params={"scope": list(scope)},
        )

    def list_capabilities(self, extension_package_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/extensions/packages/{extension_package_id}/capabilities",
            params={"scope": list(scope)},
        )

    def list_dependencies(self, extension_package_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/extensions/packages/{extension_package_id}/dependencies",
            params={"scope": list(scope)},
        )

    def check_compatibility(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/extensions/compatibility/check", json=payload)

    def get_compatibility(
        self,
        extension_compatibility_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/extensions/compatibility/{extension_compatibility_id}",
            params={"scope": list(scope)},
        )

    def review_package(
        self,
        extension_package_id: str,
        payload: JSONDict,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/extensions/packages/{extension_package_id}/review",
            json=payload,
            params={"scope": list(scope)},
        )

    def list_reviews(
        self,
        scope: Sequence[str],
        *,
        extension_package_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if extension_package_id is not None:
            params["extension_package_id"] = extension_package_id
        if decision is not None:
            params["decision"] = decision
        return self._client.get("/brain/extensions/reviews", params=params)

    def create_install_plan(self, extension_package_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/extensions/packages/{extension_package_id}/install-plan",
            json=payload,
        )

    def get_install_plan(self, install_plan_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/extensions/install-plans/{install_plan_id}",
            params={"scope": list(scope)},
        )

    def list_install_plans(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if extension_package_id is not None:
            params["extension_package_id"] = extension_package_id
        return self._client.get("/brain/extensions/install-plans", params=params)


__all__ = ["ExtensionsResource"]
