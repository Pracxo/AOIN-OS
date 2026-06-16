"""Event intake API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class EventsResource:
    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def ingest(self, event: JSONDict, *, idempotency_key: str | None = None) -> JSONValue:
        headers = {"Idempotency-Key": idempotency_key} if idempotency_key else None
        return self._client.post("/brain/events", json=event, headers=headers)
