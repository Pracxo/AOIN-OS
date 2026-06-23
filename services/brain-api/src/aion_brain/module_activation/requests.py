"""Activation request service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import AuditSink
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.audit_integrity import AuditRecordRequest
from aion_brain.contracts.module_activation import (
    ModuleActivationCreateRequest,
    ModuleActivationRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.module_activation.policy import authorize_module_activation_action
from aion_brain.module_activation.redaction import redact_activation_payload
from aion_brain.module_activation.repository import ModuleActivationRepository
from aion_brain.versioning.compatibility import emit_versioning_telemetry


class ModuleActivationRequestService:
    """Create and manage metadata-only activation requests."""

    def __init__(
        self,
        repository: ModuleActivationRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: AuditSink | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()
        self._actor_context: ActorContext | None = None

    def with_actor_context(
        self,
        actor_context: ActorContext,
    ) -> ModuleActivationRequestService:
        clone = ModuleActivationRequestService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            settings=self._settings,
        )
        clone._actor_context = actor_context
        return clone

    def create_request(self, request: ModuleActivationCreateRequest) -> ModuleActivationRequest:
        if not self._settings.module_activation_requests_enabled:
            raise RuntimeError("module_activation_requests_disabled")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.request.create",
            request.owner_scope,
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=request.workspace_id or self._workspace_id(),
            trace_id=request.trace_id or self._trace_id(),
            resource_type="module_activation_request",
            risk_level=request.risk_level,
            context={"metadata_only": True, "activation_allowed": False},
        )
        metadata = redact_activation_payload(
            {
                **request.metadata,
                "metadata_only": True,
                "activation_allowed": False,
                "execution_allowed": False,
            }
        )
        activation_request = ModuleActivationRequest(
            activation_request_id=request.activation_request_id
            or f"activation-request-{uuid4().hex}",
            trace_id=request.trace_id or self._trace_id(),
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=request.workspace_id or self._workspace_id(),
            extension_package_id=request.extension_package_id,
            module_slot_id=request.module_slot_id,
            capability_binding_ids=request.capability_binding_ids,
            readiness_assessment_ids=request.readiness_assessment_ids,
            conformance_run_ids=request.conformance_run_ids,
            status="requested",
            request_type=request.request_type,
            activation_target=request.activation_target,
            requested_mode=request.requested_mode,
            risk_level=request.risk_level,
            owner_scope=request.owner_scope,
            evidence_refs=request.evidence_refs,
            required_approvals=list(metadata.get("required_approvals", [])),
            required_policy_actions=list(metadata.get("required_policy_actions", [])),
            required_settings=list(metadata.get("required_settings", [])),
            required_sandbox_profiles=list(metadata.get("required_sandbox_profiles", [])),
            blocker_refs=[],
            activation_plan_id=None,
            registration_preview_id=None,
            rollback_plan_id=None,
            activation_allowed=False,
            execution_allowed=False,
            metadata=metadata,
            created_by=request.created_by or self._actor_id(),
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_request(activation_request)
        self._record_audit(
            "module_activation.request.create",
            saved.activation_request_id,
            "module_activation_request_created",
            saved,
        )
        self._emit(
            "module_activation_request_created",
            "module_activation_request",
            saved.activation_request_id,
            saved.owner_scope,
            {"status": saved.status, "activation_allowed": False},
        )
        return saved

    def get_request(
        self,
        activation_request_id: str,
        scope: list[str],
    ) -> ModuleActivationRequest | None:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.request.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=self._trace_id(),
            resource_type="module_activation_request",
            resource_id=activation_request_id,
        )
        item = self._repository.get_request(activation_request_id)
        return item if item is not None and _in_scope(item.owner_scope, scope) else None

    def require_request(
        self,
        activation_request_id: str,
        scope: list[str],
    ) -> ModuleActivationRequest:
        item = self.get_request(activation_request_id, scope)
        if item is None:
            raise AIONNotFoundException("module_activation_request_not_found")
        return item

    def list_requests(
        self,
        scope: list[str],
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> list[ModuleActivationRequest]:
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.request.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=self._trace_id(),
            resource_type="module_activation_request",
        )
        return [
            item
            for item in self._repository.list_requests(
                status=status,
                module_slot_id=module_slot_id,
                limit=limit,
            )
            if _in_scope(item.owner_scope, scope)
        ]

    def archive_request(
        self,
        activation_request_id: str,
        actor_id: str | None,
        reason: str,
    ) -> ModuleActivationRequest:
        item = self._repository.get_request(activation_request_id)
        if item is None:
            raise AIONNotFoundException("module_activation_request_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.request.update",
            item.owner_scope,
            actor_id=actor_id or self._actor_id(),
            workspace_id=item.workspace_id or self._workspace_id(),
            trace_id=item.trace_id or self._trace_id(),
            resource_type="module_activation_request",
            resource_id=activation_request_id,
            risk_level="medium",
            context={"reason": reason, "activation_allowed": False},
        )
        saved = self._repository.save_request(
            item.model_copy(
                update={
                    "status": "archived",
                    "archived_at": datetime.now(UTC),
                    "metadata": {
                        **item.metadata,
                        "archive_reason": reason,
                        "archived_by": actor_id,
                    },
                }
            )
        )
        self._record_audit(
            "module_activation.request.update",
            saved.activation_request_id,
            "module_activation_request_archived",
            saved,
        )
        return saved

    def soft_delete_request(
        self,
        activation_request_id: str,
        actor_id: str | None,
        reason: str,
    ) -> bool:
        item = self._repository.get_request(activation_request_id)
        if item is None:
            raise AIONNotFoundException("module_activation_request_not_found")
        authorize_module_activation_action(
            self._policy_adapter,
            "module_activation.request.delete",
            item.owner_scope,
            actor_id=actor_id or self._actor_id(),
            workspace_id=item.workspace_id or self._workspace_id(),
            trace_id=item.trace_id or self._trace_id(),
            resource_type="module_activation_request",
            resource_id=activation_request_id,
            risk_level="medium",
            context={"reason": reason, "hard_delete": False},
        )
        self._repository.save_request(
            item.model_copy(
                update={
                    "status": "deleted",
                    "deleted_at": datetime.now(UTC),
                    "metadata": {
                        **item.metadata,
                        "delete_reason": reason,
                        "deleted_by": actor_id,
                        "hard_delete": False,
                    },
                }
            )
        )
        return True

    def _record_audit(
        self,
        action_type: str,
        resource_id: str,
        event_type: str,
        request: ModuleActivationRequest,
    ) -> None:
        if self._audit_sink is None:
            return
        try:
            self._audit_sink.record(
                AuditRecordRequest(
                    trace_id=request.trace_id,
                    actor_id=request.actor_id,
                    workspace_id=request.workspace_id,
                    action_type=action_type,
                    resource_type="module_activation_request",
                    resource_id=resource_id,
                    event_type=event_type,
                    outcome="dry_run",
                    risk_level=request.risk_level,
                    source_component="module_activation",
                    payload=request.model_dump(mode="json"),
                    metadata={"activation_allowed": False, "execution_allowed": False},
                )
            )
        except Exception:
            return

    def _emit(
        self,
        event_type: str,
        node_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, object],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type=node_type,
            node_id=node_id,
            intensity=0.5,
            scope=scope,
            payload=payload,
        )

    def _actor_id(self) -> str | None:
        return self._actor_context.actor_id if self._actor_context else None

    def _workspace_id(self) -> str | None:
        return self._actor_context.workspace_id if self._actor_context else None

    def _trace_id(self) -> str | None:
        return self._actor_context.trace_id if self._actor_context else None


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(requested_scope))


__all__ = ["ModuleActivationRequestService"]
