"""Activation blocker ledger service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.module_activation import ActivationBlocker
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.redaction import redact_activation_payload
from aion_brain.module_activation.repository import ModuleActivationRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ActivationBlockerService:
    """Create and manage activation blockers."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service

    def create_blocker(
        self,
        *,
        scope: list[str],
        blocker_type: str,
        reason: str,
        recommended_action: str,
        activation_request_id: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        trace_id: str | None = None,
        severity: str = "medium",
        status: str = "open",
        missing_requirement: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ActivationBlocker:
        blocker = ActivationBlocker(
            activation_blocker_id=f"activation-blocker-{uuid4().hex}",
            trace_id=trace_id,
            activation_request_id=activation_request_id,
            module_slot_id=module_slot_id,
            capability_binding_id=capability_binding_id,
            blocker_type=blocker_type,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            status=status,  # type: ignore[arg-type]
            reason=reason,
            missing_requirement=missing_requirement,
            source_type=source_type,
            source_id=source_id,
            recommended_action=recommended_action,
            metadata=redact_activation_payload(metadata or {}),
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_blocker(blocker)
        self._emit("module_activation_blocker_created", saved, scope)
        return saved

    def list_blockers(
        self,
        scope: list[str],
        activation_request_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[ActivationBlocker]:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.blocker.read",
            scope,
            resource_type="module_activation_blocker",
        )
        return self._repository.list_blockers(
            activation_request_id=activation_request_id,
            status=status,
            severity=severity,
            limit=limit,
        )

    def dismiss_blocker(
        self,
        activation_blocker_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ActivationBlocker:
        blocker = self._repository.get_blocker(activation_blocker_id)
        if blocker is None:
            raise AIONNotFoundException("module_activation_blocker_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.blocker.update",
            ["workspace:main"],
            actor_id=actor_id,
            resource_type="module_activation_blocker",
            resource_id=activation_blocker_id,
            risk_level="medium",
            context={"reason": reason, "activation_allowed": False},
        )
        saved = self._repository.save_blocker(
            blocker.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {
                        **blocker.metadata,
                        "dismiss_reason": reason,
                        "dismissed_by": actor_id,
                        "activation_allowed": False,
                    },
                }
            )
        )
        self._emit("module_activation_blocker_dismissed", saved, ["workspace:main"])
        return saved

    def _emit(self, event_type: str, blocker: ActivationBlocker, scope: list[str]) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="module_activation_blocker",
            node_id=blocker.activation_blocker_id,
            intensity=0.6,
            scope=scope,
            payload={"blocker_type": blocker.blocker_type, "severity": blocker.severity},
        )


__all__ = ["ActivationBlockerService"]
