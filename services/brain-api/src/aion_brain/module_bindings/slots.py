"""Module slot service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.module_slots import (
    ModuleSlot,
    ModuleSlotArchiveRequest,
    ModuleSlotCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.redaction import redact_binding_payload
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.module_bindings.telemetry import emit_module_binding_telemetry


class ModuleSlotService:
    """Create and manage inactive module slots."""

    def __init__(
        self,
        repository: ModuleBindingRepository,
        policy_adapter: object,
        *,
        extension_registry_repository: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._extension_registry_repository = extension_registry_repository
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()
        self._actor_context: ActorContext | None = None

    def with_actor_context(self, actor_context: ActorContext) -> ModuleSlotService:
        """Return a context-bound clone for API use."""

        clone = ModuleSlotService(
            self._repository,
            self._policy_adapter,
            extension_registry_repository=self._extension_registry_repository,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            settings=self._settings,
        )
        clone._actor_context = actor_context
        return clone

    def create_slot(self, request: ModuleSlotCreateRequest) -> ModuleSlot:
        """Persist inactive slot metadata after policy authorization."""

        if not self._settings.module_slots_enabled:
            raise RuntimeError("module_slots_disabled")
        authorize_module_binding_action(
            self._policy_adapter,
            "module_slot.create",
            request.owner_scope,
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=request.workspace_id or self._workspace_id(),
            trace_id=request.trace_id or self._trace_id(),
            resource_type="module_slot",
            risk_level="medium",
            context={"slot_key": request.slot_key, "metadata_only": True},
        )
        now = datetime.now(UTC)
        metadata = redact_binding_payload(
            {
                **request.metadata,
                "metadata_only": True,
                "activation_allowed": False,
                "code_loading_allowed": False,
            }
        )
        slot = ModuleSlot(
            module_slot_id=request.module_slot_id or f"module-slot-{uuid4().hex}",
            trace_id=request.trace_id or self._trace_id(),
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=request.workspace_id or self._workspace_id(),
            extension_package_id=request.extension_package_id,
            slot_key=request.slot_key,
            name=request.name,
            description=request.description,
            version=request.version,
            status="proposed",
            slot_type=request.slot_type,
            lifecycle_state="metadata_only",
            owner_scope=request.owner_scope,
            compatibility_status="unknown",
            allowed_modes=request.allowed_modes,
            declared_capability_refs=request.declared_capability_refs,
            capability_binding_refs=[],
            contract_refs=request.contract_refs,
            policy_action_refs=request.policy_action_refs,
            setting_refs=request.setting_refs,
            sandbox_profile_id=request.sandbox_profile_id,
            mount_plan_id=None,
            metadata=metadata,
            created_by=request.created_by or self._actor_id(),
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_slot(slot)
        self._record_audit("module_slot.create", saved.module_slot_id, "module_slot_created", saved)
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="module_slot_created",
            node_type="module_slot",
            node_id=saved.module_slot_id,
            scope=saved.owner_scope,
            intensity=0.5,
            payload={"slot_key": saved.slot_key, "status": saved.status},
        )
        return saved

    def create_from_extension(
        self,
        extension_package_id: str,
        *,
        scope: list[str],
        created_by: str | None = None,
    ) -> ModuleSlot:
        """Create one inactive slot from an accepted extension package."""

        get_package = getattr(self._extension_registry_repository, "get_package", None)
        if not callable(get_package):
            raise AIONNotFoundException("extension_registry_unavailable")
        package = get_package(extension_package_id)
        if package is None:
            raise AIONNotFoundException("extension_package_not_found")
        return self.create_slot(
            ModuleSlotCreateRequest(
                trace_id=getattr(package, "trace_id", None),
                actor_id=getattr(package, "actor_id", None),
                workspace_id=getattr(package, "workspace_id", None),
                extension_package_id=extension_package_id,
                slot_key=cast(str, package.extension_key),
                name=cast(str, package.name),
                description=cast(str, package.description),
                version=cast(str, package.version),
                slot_type=cast(
                    Any,
                    _slot_type_from_package(getattr(package, "package_type", "generic")),
                ),
                owner_scope=scope or cast(list[str], package.owner_scope),
                allowed_modes=["dry_run"],
                declared_capability_refs=[
                    str(item.get("capability_key") or item.get("capability_id"))
                    for item in getattr(package, "declared_capabilities", [])
                    if item.get("capability_key") or item.get("capability_id")
                ],
                contract_refs=[
                    str(item.get("contract_key") or item.get("key"))
                    for item in getattr(package, "declared_contracts", [])
                    if item.get("contract_key") or item.get("key")
                ],
                policy_action_refs=list(getattr(package, "declared_policy_actions", [])),
                setting_refs=[
                    str(item.get("setting_key") or item.get("key"))
                    for item in getattr(package, "declared_settings", [])
                    if item.get("setting_key") or item.get("key")
                ],
                sandbox_profile_id=_sandbox_profile(getattr(package, "manifest", None)),
                metadata={
                    "source": "extension_registry",
                    "extension_package_id": extension_package_id,
                    "source_package_status": getattr(package, "status", None),
                },
                created_by=created_by or getattr(package, "created_by", None),
            )
        )

    def get_slot(self, module_slot_id: str, scope: list[str]) -> ModuleSlot | None:
        """Return one slot through the policy boundary."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_slot.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=self._trace_id(),
            resource_type="module_slot",
            resource_id=module_slot_id,
            risk_level="low",
        )
        return self._repository.get_slot(module_slot_id)

    def require_slot(self, module_slot_id: str, scope: list[str]) -> ModuleSlot:
        """Return one slot or raise a public not-found error."""

        slot = self.get_slot(module_slot_id, scope)
        if slot is None:
            raise AIONNotFoundException("module_slot_not_found")
        return slot

    def list_slots(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        slot_type: str | None = None,
        extension_package_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[ModuleSlot]:
        """List inactive slots."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_slot.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=self._trace_id(),
            resource_type="module_slot",
            risk_level="low",
        )
        return self._repository.list_slots(
            status=status,
            slot_type=slot_type,
            extension_package_id=extension_package_id,
            include_deleted=include_deleted,
            limit=limit,
        )

    def archive_slot(
        self,
        module_slot_id: str,
        scope: list[str],
        request: ModuleSlotArchiveRequest,
    ) -> ModuleSlot:
        """Archive an inactive slot."""

        slot = self.require_slot(module_slot_id, scope)
        authorize_module_binding_action(
            self._policy_adapter,
            "module_slot.update",
            scope,
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=slot.trace_id or self._trace_id(),
            resource_type="module_slot",
            resource_id=module_slot_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        updated = slot.model_copy(
            update={
                "status": "archived",
                "lifecycle_state": "archived",
                "archived_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "metadata": {**slot.metadata, "archive_reason": request.reason},
            }
        )
        saved = self._repository.save_slot(updated)
        self._record_audit(
            "module_slot.update", saved.module_slot_id, "module_slot_archived", saved
        )
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="module_slot_archived",
            node_type="module_slot",
            node_id=saved.module_slot_id,
            scope=saved.owner_scope,
            intensity=0.3,
            payload={"reason": request.reason},
        )
        return saved

    def soft_delete_slot(
        self,
        module_slot_id: str,
        scope: list[str],
        actor_id: str | None = None,
    ) -> ModuleSlot:
        """Soft-delete inactive slot metadata."""

        slot = self.require_slot(module_slot_id, scope)
        authorize_module_binding_action(
            self._policy_adapter,
            "module_slot.delete",
            scope,
            actor_id=actor_id or self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=slot.trace_id or self._trace_id(),
            resource_type="module_slot",
            resource_id=module_slot_id,
            risk_level="medium",
        )
        saved = self._repository.save_slot(
            slot.model_copy(
                update={
                    "status": "deleted",
                    "deleted_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        self._record_audit("module_slot.delete", saved.module_slot_id, "module_slot_deleted", saved)
        return saved

    def _record_audit(
        self,
        action_type: str,
        resource_id: str,
        event_type: str,
        slot: ModuleSlot,
    ) -> None:
        record_audit_event(
            self._audit_sink,
            action_type=action_type,
            resource_type="module_slot",
            resource_id=resource_id,
            event_type=event_type,
            outcome="completed",
            source_component="module_binding_registry",
            trace_id=slot.trace_id,
            actor_id=slot.actor_id,
            workspace_id=slot.workspace_id,
            risk_level="medium",
            payload={"slot_key": slot.slot_key, "metadata_only": True},
        )

    def _actor_id(self) -> str | None:
        return self._actor_context.actor_id if self._actor_context else None

    def _workspace_id(self) -> str | None:
        return self._actor_context.workspace_id if self._actor_context else None

    def _trace_id(self) -> str | None:
        return self._actor_context.trace_id if self._actor_context else None


def _sandbox_profile(manifest: object | None) -> str | None:
    requirements = getattr(manifest, "sandbox_requirements", None)
    if not isinstance(requirements, dict):
        return None
    value = requirements.get("profile") or requirements.get("sandbox_profile")
    return str(value) if value else None


def _slot_type_from_package(package_type: object) -> str:
    value = str(package_type or "generic")
    if value in {
        "module",
        "adapter",
        "connector",
        "capability_pack",
        "policy_pack",
        "visualization_pack",
        "generic",
    }:
        return value
    return "generic"


__all__ = ["ModuleSlotService"]
