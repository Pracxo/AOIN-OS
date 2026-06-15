"""Module Developer Kit API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ModulesResource:
    """Public module developer API wrapper."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def submit_package(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-developer/packages", json=payload)

    def list_packages(
        self,
        *,
        status: str | None = None,
        module_id: str | None = None,
    ) -> JSONValue:
        return self._client.get(
            "/brain/module-developer/packages",
            params={"status": status, "module_id": module_id},
        )

    def get_package(self, module_package_id: str) -> JSONValue:
        return self._client.get(f"/brain/module-developer/packages/{module_package_id}")

    def certify(self, module_package_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/module-developer/packages/{module_package_id}/certify",
            json=payload,
        )

    def scaffold(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-developer/scaffold", json=payload)

    def compatibility(self, module_package_id: str) -> JSONValue:
        return self._client.post(
            f"/brain/module-developer/packages/{module_package_id}/compatibility",
            json={},
        )

    def run_contract_tests(
        self,
        module_package_id: str,
        *,
        dry_run: bool = True,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-developer/packages/{module_package_id}/contract-tests/run",
            json={"dry_run": dry_run},
        )

