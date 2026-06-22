"""Policy catalog and governance API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class PolicyResource:
    """Synchronous policy governance helpers."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def list_actions(self, *, category: str | None = None, status: str | None = None) -> JSONValue:
        return self._client.get(
            "/brain/policy-catalog/actions",
            params={"category": category, "status": status},
        )

    def seed_actions(self, *, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/policy-catalog/seed-defaults",
            json={"dry_run": dry_run},
        )

    def list_permissions(
        self,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> JSONValue:
        return self._client.get(
            "/brain/policy-catalog/permissions",
            params={"category": category, "status": status},
        )

    def list_roles(self, *, status: str | None = None) -> JSONValue:
        return self._client.get(
            "/brain/policy-catalog/roles",
            params={"status": status},
        )

    def seed_roles(self, *, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/policy-catalog/roles/seed-defaults",
            json={"dry_run": dry_run},
        )

    def simulate(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/policy/simulate", json=request)

    def create_test(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/policy/tests", json=request)

    def run_tests(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/policy/tests/run", json=request)

    def coverage(self) -> JSONValue:
        return self._client.get("/brain/policy/coverage")

    def export_bundle(self, request: JSONDict) -> JSONValue:
        return self._client.post("/brain/policy/bundles/export", json=request)

    def opa_status(self) -> JSONValue:
        return self._client.get("/brain/policy/opa/status")
