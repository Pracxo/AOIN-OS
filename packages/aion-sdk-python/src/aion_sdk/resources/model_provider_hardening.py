"""Model provider hardening SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ModelProviderHardeningResource:
    """Client helpers for model provider hardening APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_profile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-providers/profiles", json=payload)

    def get_profile(self, provider_profile_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/model-providers/profiles/{provider_profile_id}",
            params={"scope": list(scope)},
        )

    def list_profiles(
        self,
        scope: Sequence[str],
        *,
        provider_key: str | None = None,
        status: str | None = None,
        risk_level: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "provider_key", provider_key)
        _set(params, "status", status)
        _set(params, "risk_level", risk_level)
        return self._client.get("/brain/model-providers/profiles", params=params)

    def seed_profiles(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-providers/profiles/seed-defaults", json=payload)

    def egress_preview(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-providers/egress-preview", json=payload)

    def simulate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-providers/simulate", json=payload)

    def assess_readiness(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-providers/readiness", json=payload)

    def blockers(
        self,
        scope: Sequence[str],
        *,
        provider_key: str | None = None,
        status: str | None = "open",
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "provider_key", provider_key)
        _set(params, "status", status)
        _set(params, "severity", severity)
        return self._client.get("/brain/model-providers/blockers", params=params)

    def dismiss_blocker(self, provider_blocker_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(
            f"/brain/model-providers/blockers/{provider_blocker_id}/dismiss",
            json=payload,
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-providers/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["ModelProviderHardeningResource"]
