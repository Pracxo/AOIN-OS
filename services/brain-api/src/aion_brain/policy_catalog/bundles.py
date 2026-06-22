"""Policy bundle export service."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import PolicyBundleExportRequest, PolicyBundleRecord
from aion_brain.contracts.secrets import reject_secret_like_keys, reject_secret_like_values
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy_catalog.repository import PolicyCatalogRepository
from aion_brain.policy_catalog.telemetry import emit_policy_telemetry


class PolicyBundleService:
    """Export versioned policy governance bundles without secrets."""

    def __init__(
        self,
        *,
        repository: PolicyCatalogRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
        version: str,
        rego_policy_path: Path | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._version = version
        self._rego_policy_path = rego_policy_path

    def export_bundle(self, request: PolicyBundleExportRequest) -> PolicyBundleRecord:
        """Export a deterministic policy bundle."""
        self._authorize("policy.bundle.export", "policy_bundle", None)
        content = self._content(request)
        reject_secret_like_keys(content)
        reject_secret_like_values(content)
        content_hash = _hash_content(content)
        bundle = PolicyBundleRecord(
            policy_bundle_id=f"policy-bundle-{uuid4().hex}",
            bundle_type=request.bundle_type,
            version=self._version,
            content_hash=content_hash,
            content=content,
            status="exported",
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_bundle(bundle)
        self._emit(
            "policy_bundle_exported",
            "bundle",
            saved.policy_bundle_id,
            0.5,
            {"bundle_type": saved.bundle_type, "content_hash": saved.content_hash},
        )
        return saved

    def get_bundle(self, policy_bundle_id: str) -> PolicyBundleRecord | None:
        """Return one bundle."""
        self._authorize("policy.bundle.export", "policy_bundle", policy_bundle_id, risk_level="low")
        return self._repository.get_bundle(policy_bundle_id)

    def list_bundles(self, bundle_type: str | None = None) -> list[PolicyBundleRecord]:
        """List bundles."""
        self._authorize("policy.bundle.export", "policy_bundle", None, risk_level="low")
        return self._repository.list_bundles(bundle_type=bundle_type)

    def _content(self, request: PolicyBundleExportRequest) -> dict[str, Any]:
        content: dict[str, Any] = {
            "version": self._version,
            "generated_at": datetime.now(UTC).isoformat(),
            "metadata": {"bundle_type": request.bundle_type},
        }
        if request.include_catalog:
            content["action_catalog"] = [
                entry.model_dump(mode="json")
                for entry in self._repository.list_actions(status=None)
            ]
        if request.include_permissions:
            content["permission_catalog"] = [
                entry.model_dump(mode="json")
                for entry in self._repository.list_permissions(status=None)
            ]
        if request.include_role_templates:
            content["role_templates"] = [
                entry.model_dump(mode="json")
                for entry in self._repository.list_role_templates(status=None)
            ]
        if request.include_tests:
            content["test_cases"] = [
                entry.model_dump(mode="json")
                for entry in self._repository.list_test_cases(status=None)
            ]
        if request.include_rego and self._rego_policy_path is not None:
            try:
                content["opa_policy_text"] = self._rego_policy_path.read_text(encoding="utf-8")
            except OSError:
                content["opa_policy_text"] = ""
        return content

    def _authorize(
        self,
        action_type: str,
        resource_type: str,
        resource_id: str | None,
        *,
        risk_level: str = "medium",
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=True,
                requested_permissions=[action_type],
                security_scope=["workspace:main"],
                context={},
            )
        )
        if not decision.allow:
            raise PermissionError(f"policy_denied:{decision.reason}")

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        intensity: float,
        payload: dict[str, Any],
    ) -> None:
        emit_policy_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=intensity,
            payload=payload,
        )


def _hash_content(content: dict[str, Any]) -> str:
    hashable = dict(content)
    hashable.pop("generated_at", None)
    normalized = json.dumps(hashable, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
