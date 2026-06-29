"""Connector simulator SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConnectorSimulatorResource:
    """Client helpers for synthetic connector dry-run simulator APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def simulate(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("simulation_type", "dry_run")
        return self._client.post("/brain/connector-simulator/simulate", json=payload)

    def replay(self, payload: JSONDict) -> JSONValue:
        payload.setdefault("fixture_type", "synthetic_replay")
        payload.setdefault("synthetic", True)
        payload.setdefault("trusted", False)
        return self._client.post("/brain/connector-simulator/replay", json=payload)

    def policy_readiness(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-simulator/policy-readiness", json=payload)

    def status(self, scope: Sequence[str]) -> JSONValue:
        return self._client.get("/brain/connector-simulator/status", params={"scope": list(scope)})

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/connector-simulator/query", json=payload)


__all__ = ["ConnectorSimulatorResource"]
