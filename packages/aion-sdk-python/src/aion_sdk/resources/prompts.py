"""Prompt Packet Compiler SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class PromptsResource:
    """Client helpers for prompt governance APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_template(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/prompts/templates", json=payload)

    def list_templates(
        self,
        scope: Sequence[str],
        *,
        status: str | None = "active",
        template_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if template_type is not None:
            params["template_type"] = template_type
        return self._client.get("/brain/prompts/templates", params=params)

    def get_template(self, prompt_template_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/prompts/templates/{prompt_template_id}",
            params={"scope": list(scope)},
        )

    def seed_templates(self, scope: Sequence[str], *, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/prompts/templates/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run},
        )

    def create_fragment(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/prompts/fragments", json=payload)

    def list_fragments(
        self,
        scope: Sequence[str],
        *,
        status: str | None = "active",
        fragment_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if fragment_type is not None:
            params["fragment_type"] = fragment_type
        return self._client.get("/brain/prompts/fragments", params=params)

    def compile(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/prompts/compile", json=payload)

    def get_packet(self, prompt_packet_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/prompts/packets/{prompt_packet_id}",
            params={"scope": list(scope)},
        )

    def list_packets(
        self,
        scope: Sequence[str],
        *,
        trace_id: str | None = None,
        status: str | None = None,
        packet_type: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if trace_id is not None:
            params["trace_id"] = trace_id
        if status is not None:
            params["status"] = status
        if packet_type is not None:
            params["packet_type"] = packet_type
        return self._client.get("/brain/prompts/packets", params=params)

    def delete_packet(self, prompt_packet_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.delete(
            f"/brain/prompts/packets/{prompt_packet_id}",
            params={"scope": list(scope)},
        )

    def boundary_check(self, prompt_packet_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            "/brain/prompts/boundary-check",
            json={"prompt_packet_id": prompt_packet_id, "scope": list(scope)},
        )

    def check_boundary(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/prompts/boundary/check", json=payload)

    def get_boundary(self, boundary_check_id: str) -> JSONValue:
        return self._client.get(f"/brain/prompts/boundary/{boundary_check_id}")

    def injection_findings(
        self,
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if trace_id is not None:
            params["trace_id"] = trace_id
        if prompt_packet_id is not None:
            params["prompt_packet_id"] = prompt_packet_id
        if severity is not None:
            params["severity"] = severity
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/prompts/injection-findings", params=params)

    def list_injections(
        self,
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self.injection_findings(
            trace_id=trace_id,
            prompt_packet_id=prompt_packet_id,
            severity=severity,
            status=status,
            limit=limit,
        )

    def preview(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/prompts/preview", json=payload)

    def get_manifest(self, model_input_manifest_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/prompts/model-input-manifests/{model_input_manifest_id}",
            params={"scope": list(scope)},
        )

    def list_manifests(
        self,
        scope: Sequence[str],
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if trace_id is not None:
            params["trace_id"] = trace_id
        if prompt_packet_id is not None:
            params["prompt_packet_id"] = prompt_packet_id
        return self._client.get("/brain/prompts/model-input-manifests", params=params)


__all__ = ["PromptsResource"]
