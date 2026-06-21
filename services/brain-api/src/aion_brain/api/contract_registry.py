"""Contract Registry API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.contracts.compatibility import (
    CompatibilityRule,
    CompatibilityScan,
    CompatibilityScanRequest,
    InterfaceDriftFinding,
)
from aion_brain.contracts.contract_registry import (
    ContractIndexRecord,
    ContractRegistryReport,
    ContractRegistryReportRequest,
    ContractSnapshot,
    ContractSnapshotCreateRequest,
    DismissFindingRequest,
    InterfaceInventoryRecord,
    MigrationNote,
    SeedCompatibilityRulesRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(prefix="/brain/contracts", tags=["contracts"])


@router.get("/contracts", response_model=list[ContractIndexRecord])
def list_contracts(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    contract_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[ContractIndexRecord]:
    try:
        return container.interface_inventory_service.with_actor_context(
            actor_context
        ).list_contracts(_scope(scope, actor_context), contract_type, status, limit)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/interfaces", response_model=list[InterfaceInventoryRecord])
def list_interfaces(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    interface_type: str | None = None,
    source_system: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[InterfaceInventoryRecord]:
    try:
        return container.interface_inventory_service.with_actor_context(
            actor_context
        ).list_interfaces(
            _scope(scope, actor_context),
            interface_type=interface_type,
            source_system=source_system,
            status=status,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/snapshots", response_model=ContractSnapshot)
def create_snapshot(
    body: ContractSnapshotCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ContractSnapshot:
    try:
        return container.contract_snapshot_service.with_actor_context(
            actor_context
        ).create_snapshot(
            _scope(body.scope, actor_context),
            snapshot_type=body.snapshot_type,
            trace_id=body.trace_id or actor_context.trace_id,
            created_by=body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/snapshots", response_model=list[ContractSnapshot])
def list_snapshots(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    snapshot_type: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[ContractSnapshot]:
    try:
        return container.contract_snapshot_service.with_actor_context(actor_context).list_snapshots(
            _scope(scope, actor_context), snapshot_type, status, limit
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/snapshots/{contract_snapshot_id}", response_model=ContractSnapshot)
def get_snapshot(
    contract_snapshot_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ContractSnapshot:
    try:
        snapshot = container.contract_snapshot_service.with_actor_context(
            actor_context
        ).get_snapshot(contract_snapshot_id, _scope(scope, actor_context))
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if snapshot is None:
        raise HTTPException(status_code=404, detail="contract_snapshot_not_found")
    return snapshot


@router.post("/rules/seed-defaults")
def seed_rules(
    body: SeedCompatibilityRulesRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    try:
        return container.compatibility_rule_service.with_actor_context(
            actor_context
        ).seed_default_rules(_scope(body.scope, actor_context), dry_run=body.dry_run)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/rules", response_model=CompatibilityRule)
def create_rule(
    body: CompatibilityRule,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompatibilityRule:
    try:
        return container.compatibility_rule_service.with_actor_context(actor_context).create_rule(
            body
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.get("/rules", response_model=list[CompatibilityRule])
def list_rules(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    rule_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[CompatibilityRule]:
    try:
        return container.compatibility_rule_service.with_actor_context(actor_context).list_rules(
            _scope(scope, actor_context),
            status=status,
            rule_type=rule_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/compatibility/scan", response_model=CompatibilityScan)
def scan_compatibility(
    body: CompatibilityScanRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompatibilityScan:
    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.compatibility_scanner.with_actor_context(actor_context).scan(request)


@router.get("/compatibility/scans/{compatibility_scan_id}", response_model=CompatibilityScan)
def get_scan(
    compatibility_scan_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CompatibilityScan:
    try:
        scan = container.contract_registry_query_service.with_actor_context(actor_context).get_scan(
            compatibility_scan_id
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    if scan is None:
        raise HTTPException(status_code=404, detail="compatibility_scan_not_found")
    return scan


@router.get("/findings", response_model=list[InterfaceDriftFinding])
def list_findings(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    severity: str | None = None,
    breaking: bool | None = None,
    interface_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 100,
) -> list[InterfaceDriftFinding]:
    try:
        return container.contract_registry_query_service.with_actor_context(
            actor_context
        ).list_findings(
            status=status,
            severity=severity,
            breaking=breaking,
            interface_type=interface_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/findings/{drift_finding_id}/dismiss", response_model=InterfaceDriftFinding)
def dismiss_finding(
    drift_finding_id: str,
    body: DismissFindingRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> InterfaceDriftFinding:
    try:
        return container.contract_registry_query_service.with_actor_context(
            actor_context
        ).dismiss_finding(drift_finding_id, body.actor_id or actor_context.actor_id, body.reason)
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/migration-notes", response_model=list[MigrationNote])
def list_migration_notes(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    note_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[MigrationNote]:
    try:
        return container.migration_note_service.with_actor_context(actor_context).list_notes(
            _scope(scope, actor_context),
            status=status,
            note_type=note_type,
            limit=limit,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


@router.post("/report", response_model=ContractRegistryReport)
def create_report(
    body: ContractRegistryReportRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ContractRegistryReport:
    try:
        return container.contract_registry_report_service.with_actor_context(
            actor_context
        ).generate(
            _scope(body.scope, actor_context),
            trace_id=body.trace_id or actor_context.trace_id,
            created_by=body.created_by or actor_context.actor_id,
        )
    except PermissionError as exc:
        raise AIONPolicyDeniedException(str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
