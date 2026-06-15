"""Health API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class HealthResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def health(self) -> JSONValue:
        return self._client.get("/health")

    def live(self) -> JSONValue:
        return self._client.get("/health/live")

    def ready(self) -> JSONValue:
        return self._client.get("/health/ready")

