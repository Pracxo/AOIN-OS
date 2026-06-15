"""Resilience SDK resource."""

from __future__ import annotations

import builtins
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ResilienceResource:
    """Client helpers for local resilience control-plane APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def status(self, scope: builtins.list[str]) -> JSONValue:
        return self._client.get("/brain/resilience/status", params={"scope": scope})

    def check_dependencies(self, scope: builtins.list[str]) -> JSONValue:
        return self._client.post(
            "/brain/resilience/dependencies/check",
            json={"scope": scope},
        )

    def list_dependencies(
        self,
        *,
        dependency_type: str | None = None,
        component: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if dependency_type is not None:
            params["dependency_type"] = dependency_type
        if component is not None:
            params["component"] = component
        return self._client.get("/brain/resilience/dependencies", params=params or None)

    def create_retry_policy(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/resilience/retry-policies", json=payload)

    def list_retry_policies(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if target_type is not None:
            params["target_type"] = target_type
        return self._client.get("/brain/resilience/retry-policies", params=params or None)

    def seed_retry_policies(self, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/resilience/retry-policies/seed-defaults",
            json={"dry_run": dry_run},
        )

    def create_circuit_breaker(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/resilience/circuit-breakers", json=payload)

    def list_circuit_breakers(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if target_type is not None:
            params["target_type"] = target_type
        return self._client.get("/brain/resilience/circuit-breakers", params=params or None)

    def reset_circuit_breaker(self, name: str, reason: str | None = None) -> JSONValue:
        payload: JSONDict = {}
        if reason is not None:
            payload["reason"] = reason
        return self._client.post(
            f"/brain/resilience/circuit-breakers/{name}/reset",
            json=payload,
        )

    def list_degraded(self, component: str | None = None) -> JSONValue:
        params = {"component": component} if component is not None else None
        return self._client.get("/brain/resilience/degraded", params=params)

    def resolve_degraded(
        self,
        degraded_event_id: str,
        reason: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {}
        if reason is not None:
            payload["reason"] = reason
        return self._client.post(
            f"/brain/resilience/degraded/{degraded_event_id}/resolve",
            json=payload,
        )

    def create_fault_rule(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/resilience/fault-rules", json=payload)

    def list_fault_rules(
        self,
        *,
        status: str | None = None,
        target_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {}
        if status is not None:
            params["status"] = status
        if target_type is not None:
            params["target_type"] = target_type
        return self._client.get("/brain/resilience/fault-rules", params=params or None)

    def disable_fault_rule(self, fault_rule_id: str, reason: str | None = None) -> JSONValue:
        payload: JSONDict = {}
        if reason is not None:
            payload["reason"] = reason
        return self._client.post(
            f"/brain/resilience/fault-rules/{fault_rule_id}/disable",
            json=payload,
        )

    def run_test(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/resilience/test/run", json=payload)

    def get_test_run(
        self,
        resilience_test_run_id: str,
        scope: builtins.list[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/resilience/test-runs/{resilience_test_run_id}",
            params={"scope": scope},
        )
