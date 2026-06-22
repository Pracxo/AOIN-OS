"""Kernel diagnostics API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class KernelResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def status(self) -> JSONValue:
        return self._client.get("/brain/kernel/status")

    def adapters(self) -> JSONValue:
        return self._client.get("/brain/kernel/adapters")

    def self_test(self, scope: list[str] | None = None, *, dry_run: bool = True) -> JSONValue:
        payload = {"scope": scope or ["workspace:main"], "dry_run": dry_run}
        return self._client.post("/brain/kernel/self-test", json=payload)

    def contracts(self) -> JSONValue:
        return self._client.get("/brain/kernel/contracts")

    def boundary_check(self) -> JSONValue:
        return self._client.post("/brain/kernel/boundary-check", json={})
