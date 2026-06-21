"""Capability binding service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.capability_bindings import (
    BindingMutationRequest,
    CapabilityBinding,
    CapabilityBindingCreateRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.redaction import redact_binding_payload
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.module_bindings.telemetry import emit_module_binding_telemetry


class CapabilityBindingService:
    """Create and manage inactive capability binding metadata."""

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

    def with_actor_context(self, actor_context: ActorContext) -> CapabilityBindingService:
        """Return a context-bound clone for API use."""

        clone = CapabilityBindingService(
            self._repository,
            self._policy_adapter,
            extension_registry_repository=self._extension_registry_repository,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            settings=self._settings,
        )
        clone._actor_context = actor_context
        return clone

    def create_binding(self, request: CapabilityBindingCreateRequest) -> CapabilityBinding:
        """Persist inactive binding metadata after policy authorization."""

        if not self._settings.capability_bindings_enabled:
            raise RuntimeError("capability_bindings_disabled")
        slot = self._repository.get_slot(request.module_slot_id)
        if slot is None:
            raise AIONNotFoundException("module_slot_not_found")
        scope = slot.owner_scope
        authorize_module_binding_action(
            self._policy_adapter,
            "capability_binding.create",
            scope,
            actor_id=request.created_by or self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=request.trace_id or slot.trace_id or self._trace_id(),
            resource_type="capability_binding",
            risk_level="medium" if request.risk_level in {"low", "medium"} else request.risk_level,
            context={"capability_key": request.capability_key, "metadata_only": True},
            approval_present=request.requires_approval,
        )
        now = datetime.now(UTC)
        metadata = redact_binding_payload(
            {
                **request.metadata,
                "metadata_only": True,
                "activation_allowed": False,
                "source_records_mutated": False,
            }
        )
        binding = CapabilityBinding(
            capability_binding_id=(
                request.capability_binding_id or f"capability-binding-{uuid4().hex}"
            ),
            trace_id=request.trace_id or slot.trace_id or self._trace_id(),
            module_slot_id=request.module_slot_id,
            extension_package_id=request.extension_package_id or slot.extension_package_id,
            capability_key=request.capability_key,
            capability_type=request.capability_type,
            binding_type=request.binding_type,
            status="proposed",
            route_key=request.route_key,
            target_runtime=request.target_runtime,
            target_ref=request.target_ref,
            risk_level=request.risk_level,
            allowed_modes=request.allowed_modes,
            input_schema=redact_binding_payload(request.input_schema),
            output_schema=redact_binding_payload(request.output_schema),
            required_policy_actions=request.required_policy_actions,
            required_settings=request.required_settings,
            required_contracts=request.required_contracts,
            requires_approval=request.requires_approval,
            requires_sandbox=request.requires_sandbox,
            sandbox_profile_id=request.sandbox_profile_id,
            dry_run_supported=request.dry_run_supported,
            controlled_supported=request.controlled_supported,
            constraints=[
                *request.constraints,
                "metadata_only",
                "capability_activation_disabled",
            ],
            metadata=metadata,
            created_by=request.created_by or self._actor_id(),
            created_at=now,
            updated_at=now,
        )
        saved = self._repository.save_binding(binding)
        refs = sorted({*slot.capability_binding_refs, saved.capability_binding_id})
        self._repository.save_slot(slot.model_copy(update={"capability_binding_refs": refs}))
        self._record_audit(
            "capability_binding.create",
            saved.capability_binding_id,
            "capability_binding_created",
            saved,
        )
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="capability_binding_created",
            node_type="capability_binding",
            node_id=saved.capability_binding_id,
            scope=scope,
            intensity=0.6,
            payload={"capability_key": saved.capability_key, "risk_level": saved.risk_level},
        )
        return saved

    def create_from_extension_capabilities(
        self,
        module_slot_id: str,
        *,
        extension_package_id: str,
        created_by: str | None = None,
    ) -> list[CapabilityBinding]:
        """Map extension-declared capabilities into inactive bindings."""

        slot = self._repository.get_slot(module_slot_id)
        if slot is None:
            raise AIONNotFoundException("module_slot_not_found")
        get_package = getattr(self._extension_registry_repository, "get_package", None)
        if not callable(get_package):
            raise AIONNotFoundException("extension_registry_unavailable")
        package = get_package(extension_package_id)
        if package is None:
            raise AIONNotFoundException("extension_package_not_found")
        created: list[CapabilityBinding] = []
        for item in getattr(package, "declared_capabilities", []):
            capability_key = str(
                item.get("capability_key")
                or item.get("capability_id")
                or f"{slot.slot_key}.capability"
            )
            risk_level = str(item.get("risk_level") or "medium")
            controlled_supported = bool(item.get("controlled_supported", False))
            created.append(
                self.create_binding(
                    CapabilityBindingCreateRequest(
                        trace_id=slot.trace_id,
                        module_slot_id=module_slot_id,
                        extension_package_id=extension_package_id,
                        capability_key=capability_key,
                        capability_type=cast(
                            Any, item.get("capability_type") or item.get("type") or "generic"
                        ),
                        binding_type="declared",
                        route_key=cast(str | None, item.get("route_key")),
                        target_runtime="metadata_only",
                        target_ref=None,
                        risk_level=cast(Any, risk_level),
                        allowed_modes=list(item.get("allowed_modes") or ["dry_run"]),
                        input_schema=dict(item.get("input_schema") or {}),
                        output_schema=dict(item.get("output_schema") or {}),
                        required_policy_actions=list(
                            item.get("required_policy_actions")
                            or getattr(package, "declared_policy_actions", [])
                        ),
                        required_settings=[
                            str(setting.get("setting_key") or setting.get("key"))
                            for setting in getattr(package, "declared_settings", [])
                            if setting.get("setting_key") or setting.get("key")
                        ],
                        required_contracts=[
                            str(contract.get("contract_key") or contract.get("key"))
                            for contract in getattr(package, "declared_contracts", [])
                            if contract.get("contract_key") or contract.get("key")
                        ],
                        requires_approval=bool(
                            item.get("requires_approval", risk_level in {"high", "critical"})
                        ),
                        requires_sandbox=bool(
                            item.get(
                                "requires_sandbox",
                                controlled_supported or risk_level in {"high", "critical"},
                            )
                        ),
                        sandbox_profile_id=slot.sandbox_profile_id,
                        dry_run_supported=bool(item.get("dry_run_supported", True)),
                        controlled_supported=controlled_supported,
                        constraints=list(item.get("constraints") or []),
                        metadata={
                            "source": "extension_registry",
                            "extension_package_id": extension_package_id,
                            "source_capability": item,
                        },
                        created_by=created_by,
                    )
                )
            )
        return created

    def get_binding(self, capability_binding_id: str, scope: list[str]) -> CapabilityBinding | None:
        """Return one inactive binding through policy."""

        authorize_module_binding_action(
            self._policy_adapter,
            "capability_binding.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=self._trace_id(),
            resource_type="capability_binding",
            resource_id=capability_binding_id,
            risk_level="low",
        )
        return self._repository.get_binding(capability_binding_id)

    def require_binding(self, capability_binding_id: str, scope: list[str]) -> CapabilityBinding:
        """Return one binding or raise not found."""

        binding = self.get_binding(capability_binding_id, scope)
        if binding is None:
            raise AIONNotFoundException("capability_binding_not_found")
        return binding

    def list_bindings(
        self,
        scope: list[str],
        *,
        module_slot_id: str | None = None,
        status: str | None = None,
        capability_type: str | None = None,
        risk_level: str | None = None,
        extension_package_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> list[CapabilityBinding]:
        """List inactive bindings."""

        authorize_module_binding_action(
            self._policy_adapter,
            "capability_binding.read",
            scope,
            actor_id=self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=self._trace_id(),
            resource_type="capability_binding",
            risk_level="low",
        )
        return self._repository.list_bindings(
            module_slot_id=module_slot_id,
            status=status,
            capability_type=capability_type,
            risk_level=risk_level,
            extension_package_id=extension_package_id,
            include_deleted=include_deleted,
            limit=limit,
        )

    def disable_binding(
        self,
        capability_binding_id: str,
        scope: list[str],
        request: BindingMutationRequest,
    ) -> CapabilityBinding:
        """Disable inactive binding metadata."""

        binding = self.require_binding(capability_binding_id, scope)
        authorize_module_binding_action(
            self._policy_adapter,
            "capability_binding.update",
            scope,
            actor_id=request.actor_id or self._actor_id(),
            workspace_id=self._workspace_id(),
            trace_id=binding.trace_id or self._trace_id(),
            resource_type="capability_binding",
            resource_id=capability_binding_id,
            risk_level="medium",
            context={"reason": request.reason},
        )
        saved = self._repository.save_binding(
            binding.model_copy(
                update={
                    "status": "disabled",
                    "disabled_at": datetime.now(UTC),
                    "updated_at": datetime.now(UTC),
                    "metadata": {**binding.metadata, "disable_reason": request.reason},
                }
            )
        )
        slot = self._repository.get_slot(saved.module_slot_id)
        scope_for_event = slot.owner_scope if slot else scope
        self._record_audit(
            "capability_binding.update",
            saved.capability_binding_id,
            "capability_binding_disabled",
            saved,
        )
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="capability_binding_disabled",
            node_type="capability_binding",
            node_id=saved.capability_binding_id,
            scope=scope_for_event,
            intensity=0.3,
            payload={"reason": request.reason},
        )
        return saved

    def _record_audit(
        self,
        action_type: str,
        resource_id: str,
        event_type: str,
        binding: CapabilityBinding,
    ) -> None:
        record_audit_event(
            self._audit_sink,
            action_type=action_type,
            resource_type="capability_binding",
            resource_id=resource_id,
            event_type=event_type,
            outcome="completed",
            source_component="module_binding_registry",
            trace_id=binding.trace_id,
            actor_id=binding.created_by,
            workspace_id=self._workspace_id(),
            risk_level=binding.risk_level,
            payload={"capability_key": binding.capability_key, "metadata_only": True},
        )

    def _actor_id(self) -> str | None:
        return self._actor_context.actor_id if self._actor_context else None

    def _workspace_id(self) -> str | None:
        return self._actor_context.workspace_id if self._actor_context else None

    def _trace_id(self) -> str | None:
        return self._actor_context.trace_id if self._actor_context else None


__all__ = ["CapabilityBindingService"]
