"""Query service for module binding registry records."""

from __future__ import annotations

from aion_brain.contracts.capability_bindings import (
    ModuleBindingQuery,
    ModuleBindingQueryResult,
)
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.repository import ModuleBindingRepository


class ModuleBindingQueryService:
    """Query inactive module slot and capability binding metadata."""

    def __init__(self, repository: ModuleBindingRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, request: ModuleBindingQuery) -> ModuleBindingQueryResult:
        """Return module binding records through AION-owned contracts."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_binding.query",
            request.scope,
            resource_type="module_binding_registry",
            risk_level="low",
            context=request.model_dump(mode="json"),
        )
        slots = self._repository.list_slots(
            status=request.status,
            extension_package_id=request.extension_package_id,
            include_deleted=request.include_deleted,
            limit=request.limit,
        )
        bindings = self._repository.list_bindings(
            module_slot_id=request.module_slot_id,
            status=request.status,
            capability_type=request.capability_type,
            risk_level=request.risk_level,
            extension_package_id=request.extension_package_id,
            include_deleted=request.include_deleted,
            limit=request.limit,
        )
        if request.query:
            query = request.query.lower()
            slots = [
                slot
                for slot in slots
                if query in slot.slot_key.lower()
                or query in slot.name.lower()
                or query in slot.description.lower()
            ]
            bindings = [
                binding
                for binding in bindings
                if query in binding.capability_key.lower()
                or query in binding.capability_type.lower()
                or query in binding.binding_type.lower()
            ]
        validation_runs = self._repository.list_validation_runs(
            module_slot_id=request.module_slot_id,
            extension_package_id=request.extension_package_id,
            limit=request.limit,
        )
        mount_plans = self._repository.list_mount_plans(
            module_slot_id=request.module_slot_id,
            limit=request.limit,
        )
        route_previews = self._repository.list_route_previews(
            module_slot_id=request.module_slot_id,
            limit=request.limit,
        )
        conflicts = self._repository.list_conflicts(
            module_slot_id=request.module_slot_id,
            limit=request.limit,
        )
        return ModuleBindingQueryResult(
            module_slots=slots,
            capability_bindings=bindings,
            validation_runs=validation_runs,
            mount_plans=mount_plans,
            route_previews=route_previews,
            conflicts=conflicts,
            total_count=(
                len(slots)
                + len(bindings)
                + len(validation_runs)
                + len(mount_plans)
                + len(route_previews)
                + len(conflicts)
            ),
            constraints=[
                "metadata_only",
                "no_module_activation",
                "no_capability_execution",
                "no_dynamic_route_registration",
            ],
            metadata={"source_mutated": False},
        )


__all__ = ["ModuleBindingQueryService"]
