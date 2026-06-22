"""Contract snapshot service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contract_registry.hash import hash_manifest
from aion_brain.contract_registry.redaction import redact_contract_payload
from aion_brain.contracts.contract_registry import (
    ContractIndexRecord,
    ContractSnapshot,
    InterfaceInventoryRecord,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class ContractSnapshotService:
    """Create and query local contract registry snapshots."""

    def __init__(
        self,
        repository: object,
        scanner: object,
        policy_adapter: object | None,
        *,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._scanner = scanner
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> ContractSnapshotService:
        return ContractSnapshotService(
            self._repository,
            self._scanner,
            self._policy_adapter,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            settings=self._settings,
            actor_context=actor_context,
        )

    def create_snapshot(
        self,
        scope: list[str],
        snapshot_type: str = "manual",
        trace_id: str | None = None,
        created_by: str | None = None,
    ) -> ContractSnapshot:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.snapshot.create",
            resource_type="contract_snapshot",
            resource_id=None,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=created_by or self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
            context={"source_mutated": False},
        )
        scan_all = getattr(self._scanner, "scan_all", None)
        scanned = scan_all(scope) if callable(scan_all) else {"contracts": [], "interfaces": []}
        contracts = _contracts(scanned.get("contracts", []))
        interfaces = _interfaces(scanned.get("interfaces", []))
        save_contract = getattr(self._repository, "save_contract", None)
        save_interface = getattr(self._repository, "save_interface", None)
        if callable(save_contract):
            for contract in contracts:
                save_contract(contract)
        if callable(save_interface):
            for interface in interfaces:
                save_interface(interface)
        manifest_items = [
            *[{"kind": "contract", **item.model_dump(mode="json")} for item in contracts],
            *[{"kind": "interface", **item.model_dump(mode="json")} for item in interfaces],
        ]
        manifest_items = [
            cast(dict[str, Any], redact_contract_payload(item)) for item in manifest_items
        ]
        manifest = cast(
            dict[str, Any],
            redact_contract_payload(
                {
                    "contracts": [
                        item for item in manifest_items if item.get("kind") == "contract"
                    ],
                    "interfaces": [
                        item for item in manifest_items if item.get("kind") == "interface"
                    ],
                }
            ),
        )
        root_hash = hash_manifest(
            sorted(manifest_items, key=lambda item: str(item.get("schema_hash")))
        )
        report = cast(
            dict[str, Any],
            redact_contract_payload(
                {
                    "warnings": scanned.get("warnings", []),
                    "source_code_is_source_of_truth": True,
                    "source_mutated": False,
                }
            ),
        )
        snapshot = ContractSnapshot(
            contract_snapshot_id=f"contract-snapshot-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            snapshot_type=snapshot_type,  # type: ignore[arg-type]
            status="created",
            version=str(getattr(self._settings, "version", "0.1.0")),
            owner_scope=scope,
            contract_count=len(contracts),
            interface_count=len(interfaces),
            policy_action_count=_count(interfaces, "interface_type", "policy_action"),
            route_count=_count(interfaces, "interface_type", "api_route")
            + _count(interfaces, "interface_type", "health_check"),
            sdk_resource_count=_count(interfaces, "interface_type", "sdk_resource"),
            cli_command_count=_count(interfaces, "interface_type", "cli_command"),
            setting_count=_count(interfaces, "interface_type", "env_setting"),
            telemetry_count=_count(interfaces, "interface_type", "telemetry_event")
            + _count(interfaces, "interface_type", "telemetry_node"),
            root_hash=root_hash,
            manifest=manifest,
            report=report,
            metadata={"source_mutated": False, "code_generated": False},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        stored = _save_snapshot(self._repository, snapshot)
        _record_audit(self._audit_sink, "contract_snapshot_created", stored.contract_snapshot_id)
        _record_provenance(
            self._provenance_service,
            "contract_snapshot",
            stored.contract_snapshot_id,
            [item.contract_key for item in contracts],
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="contract_snapshot_created",
            node_type="contract_snapshot",
            node_id=stored.contract_snapshot_id,
            intensity=0.5,
            trace_id=stored.trace_id,
            payload={"root_hash": stored.root_hash, "contract_count": stored.contract_count},
        )
        return stored

    def get_snapshot(self, contract_snapshot_id: str, scope: list[str]) -> ContractSnapshot | None:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.snapshot.read",
            resource_type="contract_snapshot",
            resource_id=contract_snapshot_id,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        get = getattr(self._repository, "get_snapshot", None)
        snapshot = get(contract_snapshot_id) if callable(get) else None
        if not isinstance(snapshot, ContractSnapshot):
            return None
        return snapshot if _scope_matches(snapshot.owner_scope, scope) else None

    def list_snapshots(
        self,
        scope: list[str],
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ContractSnapshot]:
        authorize(
            self._policy_adapter,
            action_type="contract_registry.snapshot.read",
            resource_type="contract_snapshot",
            resource_id=None,
            scope=scope,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_items = getattr(self._repository, "list_snapshots", None)
        items = (
            list_items(snapshot_type=snapshot_type, status=status, limit=limit)
            if callable(list_items)
            else []
        )
        return [item for item in items if _scope_matches(item.owner_scope, scope)]


def _contracts(value: Any) -> list[ContractIndexRecord]:
    return [item for item in value if isinstance(item, ContractIndexRecord)]


def _interfaces(value: Any) -> list[InterfaceInventoryRecord]:
    return [item for item in value if isinstance(item, InterfaceInventoryRecord)]


def _count(items: list[InterfaceInventoryRecord], attr: str, value: str) -> int:
    return sum(1 for item in items if getattr(item, attr) == value)


def _save_snapshot(repository: object, snapshot: ContractSnapshot) -> ContractSnapshot:
    save = getattr(repository, "save_snapshot", None)
    stored = save(snapshot) if callable(save) else snapshot
    return stored if isinstance(stored, ContractSnapshot) else snapshot


def _scope_matches(owner_scope: list[str], scope: list[str]) -> bool:
    return bool(set(owner_scope).intersection(scope))


def _record_audit(audit_sink: object | None, event_type: str, resource_id: str) -> None:
    record = getattr(audit_sink, "record", None) or getattr(audit_sink, "record_event", None)
    if callable(record):
        try:
            record(event_type=event_type, resource_id=resource_id)
        except Exception:
            return


def _record_provenance(
    provenance_service: object | None,
    source_type: str,
    source_id: str,
    target_refs: list[str],
) -> None:
    link = getattr(provenance_service, "link", None) or getattr(provenance_service, "record", None)
    if callable(link):
        try:
            link(source_type=source_type, source_id=source_id, target_refs=target_refs)
        except Exception:
            return


__all__ = ["ContractSnapshotService"]
