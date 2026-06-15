"""Secret reference vault service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.secrets import SecretRef, SecretRefCreateRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.secrets.redaction import (
    reject_secret_like_keys,
    reject_secret_like_values,
)
from aion_brain.secrets.repository import SecretRefRepository


class SecretRefService:
    """Manage metadata-only secret references."""

    def __init__(
        self,
        *,
        repository: SecretRefRepository,
        policy_adapter: PolicyAdapter,
        telemetry_service: object | None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_secret_ref(self, request: SecretRefCreateRequest) -> SecretRef:
        """Create a metadata-only secret reference."""
        self._authorize(
            "secret_ref.create",
            request.secret_ref_id,
            "medium",
            request.owner_scope,
            actor_id=request.created_by,
            approval_present=True,
        )
        now = datetime.now(UTC)
        secret_ref = SecretRef(
            secret_ref_id=request.secret_ref_id or f"secret-ref-{uuid4().hex}",
            name=request.name,
            description=request.description,
            status="active",
            owner_scope=request.owner_scope,
            secret_type=request.secret_type,
            provider=request.provider,
            external_ref=request.external_ref,
            sensitivity=request.sensitivity,
            rotation_policy=request.rotation_policy,
            metadata=request.metadata,
            created_by=request.created_by,
            created_at=now,
            updated_at=now,
            disabled_at=None,
            last_rotated_at=None,
        )
        saved = self._repository.save(secret_ref)
        self._emit("secret_ref_created", "secret_ref", saved.secret_ref_id, 0.5, {})
        return saved

    def get_secret_ref(self, secret_ref_id: str, scope: list[str]) -> SecretRef | None:
        """Return one secret reference without raw material."""
        self._authorize("secret_ref.read", secret_ref_id, "low", scope)
        secret_ref = self._repository.get(secret_ref_id)
        if secret_ref is None or not _scope_matches(secret_ref.owner_scope, scope):
            return None
        return secret_ref

    def list_secret_refs(self, scope: list[str], status: str | None = None) -> list[SecretRef]:
        """List visible secret references."""
        self._authorize("secret_ref.read", None, "low", scope)
        return [
            secret_ref
            for secret_ref in self._repository.list(status)
            if _scope_matches(secret_ref.owner_scope, scope)
        ]

    def disable_secret_ref(
        self,
        secret_ref_id: str,
        actor_id: str | None,
        reason: str,
    ) -> SecretRef:
        """Disable a secret reference."""
        secret_ref = self._repository.get(secret_ref_id)
        if secret_ref is None:
            raise ValueError("secret_ref_not_found")
        self._authorize(
            "secret_ref.disable",
            secret_ref_id,
            "medium",
            secret_ref.owner_scope,
            actor_id=actor_id,
            approval_present=True,
        )
        now = datetime.now(UTC)
        saved = self._repository.save(
            secret_ref.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": now,
                    "updated_at": now,
                    "metadata": {**secret_ref.metadata, "disabled_reason": reason},
                }
            )
        )
        self._emit("secret_ref_disabled", "secret_ref", saved.secret_ref_id, 0.7, {})
        return saved

    def rotate_metadata(
        self,
        secret_ref_id: str,
        actor_id: str | None,
        metadata: dict[str, Any],
    ) -> SecretRef:
        """Update rotation metadata without storing secret values."""
        reject_secret_like_keys(metadata)
        reject_secret_like_values(metadata)
        secret_ref = self._repository.get(secret_ref_id)
        if secret_ref is None:
            raise ValueError("secret_ref_not_found")
        self._authorize(
            "secret_ref.rotate",
            secret_ref_id,
            "medium",
            secret_ref.owner_scope,
            actor_id=actor_id,
            approval_present=True,
        )
        now = datetime.now(UTC)
        saved = self._repository.save(
            secret_ref.model_copy(
                update={
                    "metadata": {**secret_ref.metadata, **metadata},
                    "last_rotated_at": now,
                    "updated_at": now,
                }
            )
        )
        self._emit("secret_ref_rotated", "secret_ref", saved.secret_ref_id, 0.6, {})
        return saved

    def _authorize(
        self,
        action_type: str,
        resource_id: str | None,
        risk_level: str,
        scope: list[str],
        *,
        actor_id: str | None = None,
        approval_present: bool = False,
    ) -> None:
        decision = self._policy_adapter.authorize(
            PolicyRequest(
                request_id=f"{action_type}-{resource_id or uuid4().hex}",
                trace_id=None,
                actor_id=actor_id,
                workspace_id=None,
                action_type=action_type,
                resource_type="secret_ref",
                resource_id=resource_id,
                risk_level=risk_level,
                approval_present=approval_present,
                requested_permissions=[action_type],
                security_scope=scope,
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
        emit = getattr(self._telemetry_service, "emit", None)
        if not callable(emit):
            return
        try:
            emit(
                VisualTelemetryEvent(
                    telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                    trace_id=node_id,
                    event_type=cast(Any, event_type),
                    node_type=cast(Any, node_type),
                    node_id=node_id,
                    edge_from=None,
                    edge_to=node_id,
                    intensity=intensity,
                    payload=payload,
                    created_at=datetime.now(UTC),
                )
            )
        except Exception:
            return


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope).intersection(set(requested_scope)))
