"""Interface inventory service for AION Contract Registry."""

from __future__ import annotations

from aion_brain.contracts.contract_registry import ContractIndexRecord, InterfaceInventoryRecord
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class InterfaceInventoryService:
    """Upsert and query contract registry index records."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> InterfaceInventoryService:
        return InterfaceInventoryService(
            self._repository,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            actor_context=actor_context,
        )

    def upsert_contract(self, record: ContractIndexRecord) -> ContractIndexRecord:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.resource.create",
            resource_type="contract",
            resource_id=record.contract_key,
            scope=record.owner_scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"source_mutated": False},
        )
        save = getattr(self._repository, "save_contract", None)
        stored = save(record) if callable(save) else record
        emit_telemetry(
            self._telemetry_service,
            event_type="contract_indexed",
            node_type="contract",
            node_id=stored.contract_index_id,
            intensity=0.4,
            trace_id=self._actor_context.trace_id,
            payload={"contract_key": stored.contract_key, "contract_type": stored.contract_type},
        )
        return stored

    def upsert_interface(self, record: InterfaceInventoryRecord) -> InterfaceInventoryRecord:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.resource.create",
            resource_type="interface",
            resource_id=record.interface_key,
            scope=record.owner_scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"source_mutated": False},
        )
        save = getattr(self._repository, "save_interface", None)
        stored = save(record) if callable(save) else record
        emit_telemetry(
            self._telemetry_service,
            event_type="interface_indexed",
            node_type="interface",
            node_id=stored.interface_id,
            intensity=0.4,
            trace_id=self._actor_context.trace_id,
            payload={
                "interface_key": stored.interface_key,
                "interface_type": stored.interface_type,
            },
        )
        return stored

    def list_contracts(
        self,
        scope: list[str],
        contract_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ContractIndexRecord]:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.resource.read",
            resource_type="contract",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_contracts", None)
        items = (
            list_items(contract_type=contract_type, status=status, limit=limit)
            if callable(list_items)
            else []
        )
        return [item for item in items if _scope_matches(item.owner_scope, scope)]

    def list_interfaces(
        self,
        scope: list[str],
        interface_type: str | None = None,
        source_system: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[InterfaceInventoryRecord]:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.interface.read",
            resource_type="interface",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_interfaces", None)
        items = (
            list_items(
                interface_type=interface_type,
                source_system=source_system,
                status=status,
                limit=limit,
            )
            if callable(list_items)
            else []
        )
        return [item for item in items if _scope_matches(item.owner_scope, scope)]


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


__all__ = ["InterfaceInventoryService"]
