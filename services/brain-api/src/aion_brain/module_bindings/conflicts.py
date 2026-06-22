"""Conflict detection for inactive module bindings."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.capability_bindings import (
    BindingConflict,
    BindingMutationRequest,
    CapabilityBinding,
)
from aion_brain.module_bindings.policy import authorize_module_binding_action
from aion_brain.module_bindings.repository import ModuleBindingRepository
from aion_brain.module_bindings.telemetry import emit_module_binding_telemetry


class BindingConflictService:
    """Detect and manage binding conflicts without changing source records."""

    def __init__(
        self,
        repository: ModuleBindingRepository,
        policy_adapter: object,
        *,
        contract_repository: object | None = None,
        policy_catalog_repository: object | None = None,
        settings: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._contract_repository = contract_repository
        self._policy_catalog_repository = policy_catalog_repository
        self._settings = settings
        self._telemetry_service = telemetry_service

    def detect_conflicts(
        self,
        scope: list[str],
        *,
        module_slot_id: str | None = None,
        capability_binding_ids: list[str] | None = None,
        trace_id: str | None = None,
    ) -> list[BindingConflict]:
        """Return deterministic conflicts for slots and bindings."""

        bindings = self._bindings_for(module_slot_id, capability_binding_ids or [])
        conflicts: list[BindingConflict] = []
        seen: dict[str, list[CapabilityBinding]] = {}
        for binding in bindings:
            if binding.status in {"disabled", "archived"}:
                continue
            seen.setdefault(binding.capability_key, []).append(binding)
        for capability_key, grouped in seen.items():
            if len(grouped) > 1:
                conflicts.append(
                    self._conflict(
                        "duplicate_capability_key",
                        "high",
                        "Duplicate capability key declared in module bindings.",
                        [item.capability_binding_id for item in grouped],
                        "Disable or rename duplicate inactive bindings before activation work.",
                        module_slot_id=module_slot_id,
                        capability_binding_id=grouped[0].capability_binding_id,
                        trace_id=trace_id,
                        metadata={"capability_key": capability_key},
                    )
                )
        for binding in bindings:
            conflicts.extend(self._binding_conflicts(binding, trace_id=trace_id))
        for conflict in conflicts:
            emit_module_binding_telemetry(
                self._telemetry_service,
                event_type="binding_conflict_detected",
                node_type="binding_conflict",
                node_id=conflict.binding_conflict_id,
                scope=scope,
                intensity=0.8 if conflict.severity in {"high", "critical"} else 0.5,
                payload={
                    "conflict_type": conflict.conflict_type,
                    "severity": conflict.severity,
                },
            )
        return conflicts

    def save_conflicts(self, conflicts: list[BindingConflict]) -> list[BindingConflict]:
        """Persist detected conflicts."""

        return [self._repository.save_conflict(conflict) for conflict in conflicts]

    def list_conflicts(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> list[BindingConflict]:
        """List conflicts through the policy boundary."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_binding.conflict.read",
            scope,
            resource_type="binding_conflict",
            risk_level="low",
        )
        return self._repository.list_conflicts(
            status=status,
            severity=severity,
            module_slot_id=module_slot_id,
            capability_binding_id=capability_binding_id,
            limit=limit,
        )

    def dismiss_conflict(
        self,
        binding_conflict_id: str,
        scope: list[str],
        request: BindingMutationRequest,
    ) -> BindingConflict:
        """Mark one conflict dismissed."""

        authorize_module_binding_action(
            self._policy_adapter,
            "module_binding.conflict.update",
            scope,
            actor_id=request.actor_id,
            resource_type="binding_conflict",
            resource_id=binding_conflict_id,
            risk_level="medium",
        )
        conflict = self._repository.get_conflict(binding_conflict_id)
        if conflict is None:
            raise AIONNotFoundException("binding_conflict_not_found")
        return self._repository.save_conflict(
            conflict.model_copy(
                update={
                    "status": "dismissed",
                    "dismissed_at": datetime.now(UTC),
                    "metadata": {**conflict.metadata, "dismiss_reason": request.reason},
                }
            )
        )

    def _bindings_for(
        self,
        module_slot_id: str | None,
        capability_binding_ids: list[str],
    ) -> list[CapabilityBinding]:
        if capability_binding_ids:
            return [
                binding
                for binding_id in capability_binding_ids
                if (binding := self._repository.get_binding(binding_id)) is not None
            ]
        return self._repository.list_bindings(module_slot_id=module_slot_id, limit=1000)

    def _binding_conflicts(
        self,
        binding: CapabilityBinding,
        *,
        trace_id: str | None,
    ) -> list[BindingConflict]:
        conflicts: list[BindingConflict] = []
        for contract_key in binding.required_contracts:
            if not self._contract_exists(contract_key):
                conflicts.append(
                    self._conflict(
                        "missing_contract",
                        "high",
                        "Required contract is not present in the local contract registry.",
                        [binding.capability_binding_id, contract_key],
                        "Register or update the required AION contract before mounting.",
                        module_slot_id=binding.module_slot_id,
                        capability_binding_id=binding.capability_binding_id,
                        trace_id=trace_id or binding.trace_id,
                        metadata={"contract_key": contract_key},
                    )
                )
        for action_type in binding.required_policy_actions:
            if not self._policy_action_exists(action_type):
                conflicts.append(
                    self._conflict(
                        "missing_policy_action",
                        "high",
                        "Required policy action is not present in the local policy catalog.",
                        [binding.capability_binding_id, action_type],
                        "Add the generic policy action before mounting.",
                        module_slot_id=binding.module_slot_id,
                        capability_binding_id=binding.capability_binding_id,
                        trace_id=trace_id or binding.trace_id,
                        metadata={"action_type": action_type},
                    )
                )
        for setting_key in binding.required_settings:
            if not self._setting_exists(setting_key):
                conflicts.append(
                    self._conflict(
                        "missing_setting",
                        "medium",
                        "Required setting is not configured on the Brain settings object.",
                        [binding.capability_binding_id, setting_key],
                        "Add or rename the required feature flag or setting.",
                        module_slot_id=binding.module_slot_id,
                        capability_binding_id=binding.capability_binding_id,
                        trace_id=trace_id or binding.trace_id,
                        metadata={"setting_key": setting_key},
                    )
                )
        if binding.controlled_supported and not binding.requires_sandbox:
            conflicts.append(
                self._conflict(
                    "sandbox_required",
                    "high",
                    "Controlled bindings require an explicit sandbox boundary.",
                    [binding.capability_binding_id],
                    "Require sandbox execution before controlled mode is allowed.",
                    module_slot_id=binding.module_slot_id,
                    capability_binding_id=binding.capability_binding_id,
                    trace_id=trace_id or binding.trace_id,
                )
            )
        if binding.controlled_supported and not binding.sandbox_profile_id:
            conflicts.append(
                self._conflict(
                    "sandbox_required",
                    "medium",
                    "Controlled binding has no sandbox profile metadata.",
                    [binding.capability_binding_id],
                    "Attach a sandbox profile reference before mounting.",
                    module_slot_id=binding.module_slot_id,
                    capability_binding_id=binding.capability_binding_id,
                    trace_id=trace_id or binding.trace_id,
                )
            )
        if binding.route_key and not bool(
            getattr(self._settings, "dynamic_route_registration_enabled", False)
        ):
            conflicts.append(
                self._conflict(
                    "route_registration_disabled",
                    "high",
                    "Dynamic route registration is disabled for v0.1.",
                    [binding.capability_binding_id, binding.route_key],
                    "Keep route binding as preview metadata only.",
                    module_slot_id=binding.module_slot_id,
                    capability_binding_id=binding.capability_binding_id,
                    trace_id=trace_id or binding.trace_id,
                    metadata={"route_key": binding.route_key},
                )
            )
        if binding.risk_level in {"high", "critical"} and not binding.requires_approval:
            conflicts.append(
                self._conflict(
                    "high_risk_requires_review",
                    "critical",
                    "High-risk and critical bindings require approval metadata.",
                    [binding.capability_binding_id],
                    "Record review and approval metadata before mounting.",
                    module_slot_id=binding.module_slot_id,
                    capability_binding_id=binding.capability_binding_id,
                    trace_id=trace_id or binding.trace_id,
                )
            )
        if _activation_requested(binding.metadata) or bool(
            getattr(self._settings, "capability_binding_activation_enabled", False)
        ):
            conflicts.append(
                self._conflict(
                    "activation_disabled",
                    "critical",
                    "Capability binding activation is disabled in v0.1.",
                    [binding.capability_binding_id],
                    "Remove activation metadata and keep the record inactive.",
                    module_slot_id=binding.module_slot_id,
                    capability_binding_id=binding.capability_binding_id,
                    trace_id=trace_id or binding.trace_id,
                )
            )
        return conflicts

    def _contract_exists(self, contract_key: str) -> bool:
        if self._contract_repository is None:
            return False
        list_contracts = getattr(self._contract_repository, "list_contracts", None)
        if not callable(list_contracts):
            return False
        try:
            contracts = list_contracts(status="active", limit=5000)
        except TypeError:
            contracts = list_contracts(limit=5000)
        return any(getattr(item, "contract_key", None) == contract_key for item in contracts)

    def _policy_action_exists(self, action_type: str) -> bool:
        if self._policy_catalog_repository is None:
            return False
        get_action = getattr(self._policy_catalog_repository, "get_action", None)
        if callable(get_action):
            return get_action(action_type) is not None
        list_actions = getattr(self._policy_catalog_repository, "list_actions", None)
        if callable(list_actions):
            try:
                return any(
                    getattr(item, "action_type", None) == action_type for item in list_actions()
                )
            except TypeError:
                return any(
                    getattr(item, "action_type", None) == action_type
                    for item in list_actions(status=None)
                )
        return False

    def _setting_exists(self, setting_key: str) -> bool:
        if self._settings is None:
            return False
        return hasattr(self._settings, setting_key)

    def _conflict(
        self,
        conflict_type: str,
        severity: str,
        reason: str,
        refs: list[str],
        recommended_action: str,
        *,
        module_slot_id: str | None,
        capability_binding_id: str | None,
        trace_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> BindingConflict:
        return BindingConflict(
            binding_conflict_id=f"binding-conflict-{uuid4().hex}",
            trace_id=trace_id,
            module_slot_id=module_slot_id,
            capability_binding_id=capability_binding_id,
            conflict_type=cast(Any, conflict_type),
            severity=cast(Any, severity),
            status="open",
            reason=reason,
            conflicting_refs=refs,
            recommended_action=recommended_action,
            metadata=metadata or {},
            created_at=datetime.now(UTC),
        )


def _activation_requested(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in {"activate", "active", "activation", "load_code", "dynamic_route"}:
                return True
            if _activation_requested(nested):
                return True
    if isinstance(value, list):
        return any(_activation_requested(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(marker in lowered for marker in ("activate", "activation", "load_code"))
    return False


__all__ = ["BindingConflictService"]
