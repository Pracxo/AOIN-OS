"""Capability conformance SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ConformanceResource:
    """Client helpers for conformance and readiness APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_profile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/conformance/profiles", json=payload)

    def get_profile(self, conformance_profile_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/conformance/profiles/{conformance_profile_id}",
            params={"scope": list(scope)},
        )

    def list_profiles(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        profile_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "profile_type", profile_type)
        return self._client.get("/brain/conformance/profiles", params=params)

    def seed_default_profiles(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
    ) -> JSONValue:
        return self._client.post(
            "/brain/conformance/profiles/seed-defaults",
            params={"scope": list(scope), "dry_run": dry_run},
        )

    def create_test_vector(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/conformance/test-vectors", json=payload)

    def get_test_vector(self, test_vector_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/conformance/test-vectors/{test_vector_id}",
            params={"scope": list(scope)},
        )

    def list_test_vectors(
        self,
        scope: Sequence[str],
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        extension_package_id: str | None = None,
        status: str | None = None,
        vector_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "module_slot_id", module_slot_id)
        _set(params, "capability_binding_id", capability_binding_id)
        _set(params, "extension_package_id", extension_package_id)
        _set(params, "status", status)
        _set(params, "vector_type", vector_type)
        return self._client.get("/brain/conformance/test-vectors", params=params)

    def generate_test_vectors(
        self,
        capability_binding_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/conformance/test-vectors/generate-for-binding/{capability_binding_id}",
            params={"scope": list(scope)},
        )

    def run(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/conformance/run", json=payload)

    def get_run(self, conformance_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/conformance/runs/{conformance_run_id}")

    def list_findings(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        finding_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "severity", severity)
        _set(params, "finding_type", finding_type)
        return self._client.get("/brain/conformance/findings", params=params)

    def dismiss_finding(
        self,
        conformance_finding_id: str,
        payload: JSONDict,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/conformance/findings/{conformance_finding_id}/dismiss",
            json=payload,
            params={"scope": list(scope)},
        )

    def assess_readiness(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/readiness/assess", json=payload)

    def get_readiness_assessment(
        self,
        readiness_assessment_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/readiness/assessments/{readiness_assessment_id}",
            params={"scope": list(scope)},
        )

    def list_readiness_assessments(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        readiness_level: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "readiness_level", readiness_level)
        return self._client.get("/brain/readiness/assessments", params=params)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/conformance/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["ConformanceResource"]
