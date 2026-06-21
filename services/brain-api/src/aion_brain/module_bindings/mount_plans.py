"""Non-executable module mount plan service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.capability_bindings import (
    BindingMutationRequest,
    ModuleMountPlan,
    MountPlanCreateRequest,
)
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.module_bindings.telemetry import emit_module_binding_telemetry


class ModuleMountPlanService:
    """Create future mount plans without execution or activation."""

    def __init__(
        self,
        repository: ModuleBindingRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings or get_settings()

    def create_plan(self, request: MountPlanCreateRequest) -> ModuleMountPlan:
        """Create a non-executable future module mount plan."""

        if not self._settings.module_mount_plans_enabled:
            raise RuntimeError("module_mount_plans_disabled")
        slot = self._repository.get_slot(request.module_slot_id)
        if slot is None:
            raise AIONNotFoundException("module_slot_not_found")
        scope = request.scope or slot.owner_scope
        authorize_module_binding_action(
            self._policy_adapter,
            "module_mount_plan.create",
            scope,
            actor_id=request.created_by,
            workspace_id=slot.workspace_id,
            trace_id=slot.trace_id,
            resource_type="module_mount_plan",
            resource_id=request.module_slot_id,
            risk_level="medium",
        )
        bindings = self._repository.list_bindings(module_slot_id=slot.module_slot_id, limit=1000)
        required_contracts = sorted(
            {ref for binding in bindings for ref in binding.required_contracts}
        )
        required_policy_actions = sorted(
            {ref for binding in bindings for ref in binding.required_policy_actions}
        )
        required_settings = sorted(
            {ref for binding in bindings for ref in binding.required_settings}
        )
        required_sandbox_profiles = sorted(
            {
                ref
                for binding in bindings
                for ref in [binding.sandbox_profile_id or slot.sandbox_profile_id]
                if ref
            }
        )
        blockers = _mount_blockers(self._settings)
        plan = ModuleMountPlan(
            mount_plan_id=f"module-mount-plan-{uuid4().hex}",
            trace_id=slot.trace_id,
            module_slot_id=slot.module_slot_id,
            extension_package_id=slot.extension_package_id,
            status=cast(Any, "blocked" if blockers else "created"),
            plan_type="mount_preview",
            owner_scope=scope,
            steps=[
                _step("read_module_slot", "metadata_only"),
                _step("read_capability_bindings", "metadata_only"),
                _step("validate_contract_refs", "metadata_only"),
                _step("validate_policy_actions", "metadata_only"),
                _step("validate_sandbox_metadata", "metadata_only"),
                _step("prepare_future_mount", "blocked"),
            ],
            required_contracts=required_contracts,
            required_policy_actions=required_policy_actions,
            required_settings=required_settings,
            required_sandbox_profiles=required_sandbox_profiles,
            capability_binding_ids=[binding.capability_binding_id for binding in bindings],
            blocked=bool(blockers),
            blockers=blockers,
            warnings=[
                {
                    "code": "activation_reserved",
                    "severity": "medium",
                    "message": "Module activation is reserved for a later AION task.",
                }
            ],
            executable=False,
            execution_allowed=False,
            metadata={
                "metadata_only": True,
                "source_records_mutated": False,
                "activation_allowed": False,
                "code_loading_allowed": False,
            },
            created_by=request.created_by,
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_mount_plan(plan)
        self._repository.save_slot(
            slot.model_copy(
                update={
                    "mount_plan_id": saved.mount_plan_id,
                    "lifecycle_state": "mount_planned",
                    "updated_at": datetime.now(UTC),
                }
            )
        )
        self._record_audit(saved)
        emit_module_binding_telemetry(
            self._telemetry_service,
            event_type="module_mount_plan_created",
            node_type="module_mount_plan",
            node_id=saved.mount_plan_id,
            scope=saved.owner_scope,
            intensity=0.5,
            payload={"blocked": saved.blocked, "module_slot_id": saved.module_slot_id},
        )
        return saved

    def get_plan(self, mount_plan_id: str, scope: list[str]) -> ModuleMountPlan | None:
        """Return one mount plan through policy."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_mount_plan.read",
            scope,
            resource_type="module_mount_plan",
            resource_id=mount_plan_id,
            risk_level="low",
        )
        return self._repository.get_mount_plan(mount_plan_id)

    def require_plan(self, mount_plan_id: str, scope: list[str]) -> ModuleMountPlan:
        """Return one plan or raise not found."""

        plan = self.get_plan(mount_plan_id, scope)
        if plan is None:
            raise AIONNotFoundException("module_mount_plan_not_found")
        return plan

    def list_plans(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> list[ModuleMountPlan]:
        """List mount plans."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_mount_plan.read",
            scope,
            resource_type="module_mount_plan",
            risk_level="low",
        )
        return self._repository.list_mount_plans(
            status=status,
            module_slot_id=module_slot_id,
            limit=limit,
        )

    def archive_plan(
        self,
        mount_plan_id: str,
        scope: list[str],
        request: BindingMutationRequest,
    ) -> ModuleMountPlan:
        """Archive one mount plan."""

        plan = self.require_plan(mount_plan_id, scope)
        authorize_module_binding_action(
            self._policy_adapter,
            "module_mount_plan.update",
            scope,
            actor_id=request.actor_id,
            trace_id=plan.trace_id,
            resource_type="module_mount_plan",
            resource_id=mount_plan_id,
            risk_level="medium",
        )
        return self._repository.save_mount_plan(
            plan.model_copy(
                update={
                    "status": "archived",
                    "archived_at": datetime.now(UTC),
                    "metadata": {**plan.metadata, "archive_reason": request.reason},
                }
            )
        )

    def _record_audit(self, plan: ModuleMountPlan) -> None:
        record_audit_event(
            self._audit_sink,
            action_type="module_mount_plan.create",
            resource_type="module_mount_plan",
            resource_id=plan.mount_plan_id,
            event_type="module_mount_plan_created",
            outcome="blocked" if plan.blocked else "completed",
            source_component="module_binding_registry",
            trace_id=plan.trace_id,
            risk_level="medium",
            payload={"module_slot_id": plan.module_slot_id, "metadata_only": True},
        )


def _mount_blockers(settings: Settings) -> list[dict[str, Any]]:
    blockers = [
        {
            "code": "mount_execution_not_implemented",
            "severity": "high",
            "message": "Module mount execution is reserved for a later AION task.",
        }
    ]
    if bool(getattr(settings, "module_slot_activation_enabled", False)):
        blockers.append(
            {
                "code": "module_slot_activation_enabled",
                "severity": "critical",
                "message": "Module slot activation must remain disabled in v0.1.",
            }
        )
    return blockers


def _step(step: str, status: str) -> dict[str, Any]:
    return {"step": step, "status": status, "executable": False}


__all__ = ["ModuleMountPlanService"]
