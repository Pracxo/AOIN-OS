"""Policy catalog, simulation, test, coverage, and bundle APIs."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.policy_catalog import (
    OPAStatus,
    PermissionCatalogEntry,
    PolicyActionCatalogEntry,
    PolicyBundleExportRequest,
    PolicyBundleRecord,
    PolicyCoverageReport,
    PolicySimulationRequest,
    PolicySimulationResult,
    PolicyTestCase,
    PolicyTestRun,
    PolicyTestRunRequest,
    RoleTemplate,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.policy_catalog.bundles import PolicyBundleService
from aion_brain.policy_catalog.catalog import PolicyCatalogService
from aion_brain.policy_catalog.coverage import PolicyCoverageAnalyzer
from aion_brain.policy_catalog.permissions import PermissionMatrixService
from aion_brain.policy_catalog.simulation import PolicySimulationService
from aion_brain.policy_catalog.test_harness import PolicyTestHarness

router = APIRouter(tags=["policy-catalog"])


class DisableCatalogItemRequest(BaseModel):
    """Disable catalog item request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class SeedDefaultsRequest(BaseModel):
    """Seed defaults request."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True


def get_kernel_container(request: Request) -> KernelContainer:
    """Return kernel container."""
    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


def get_policy_catalog_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PolicyCatalogService:
    """Return policy catalog service."""
    return container.policy_catalog_service


def get_permission_matrix_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PermissionMatrixService:
    """Return permission matrix service."""
    return container.permission_matrix_service


def get_policy_simulation_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PolicySimulationService:
    """Return policy simulation service."""
    return container.policy_simulation_service


def get_policy_test_harness(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PolicyTestHarness:
    """Return policy test harness."""
    return container.policy_test_harness


def get_policy_coverage_analyzer(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PolicyCoverageAnalyzer:
    """Return policy coverage analyzer."""
    return container.policy_coverage_analyzer


def get_policy_bundle_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PolicyBundleService:
    """Return policy bundle service."""
    return container.policy_bundle_service


@router.post("/brain/policy-catalog/actions", response_model=PolicyActionCatalogEntry)
def create_action(
    body: PolicyActionCatalogEntry,
    service: Annotated[PolicyCatalogService, Depends(get_policy_catalog_service)],
) -> PolicyActionCatalogEntry:
    """Create a policy action catalog entry."""
    try:
        return service.create_action(body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/brain/policy-catalog/actions", response_model=list[PolicyActionCatalogEntry])
def list_actions(
    service: Annotated[PolicyCatalogService, Depends(get_policy_catalog_service)],
    category: str | None = None,
    status: str | None = None,
) -> list[PolicyActionCatalogEntry]:
    """List policy action catalog entries."""
    return service.list_actions(category=category, status=status)


@router.get("/brain/policy-catalog/actions/{action_type}", response_model=PolicyActionCatalogEntry)
def get_action(
    action_type: str,
    service: Annotated[PolicyCatalogService, Depends(get_policy_catalog_service)],
) -> PolicyActionCatalogEntry:
    """Get a policy action catalog entry."""
    entry = service.get_action(action_type)
    if entry is None:
        raise HTTPException(status_code=404, detail="policy_action_not_found")
    return entry


@router.post(
    "/brain/policy-catalog/actions/{action_type}/disable",
    response_model=PolicyActionCatalogEntry,
)
def disable_action(
    action_type: str,
    body: DisableCatalogItemRequest,
    service: Annotated[PolicyCatalogService, Depends(get_policy_catalog_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PolicyActionCatalogEntry:
    """Disable a policy action catalog entry."""
    try:
        return service.disable_action(
            action_type,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/brain/policy-catalog/seed-defaults")
def seed_action_defaults(
    body: SeedDefaultsRequest,
    service: Annotated[PolicyCatalogService, Depends(get_policy_catalog_service)],
) -> dict[str, object]:
    """Seed default policy action catalog entries."""
    return service.seed_defaults(dry_run=body.dry_run)


@router.post("/brain/policy-catalog/permissions", response_model=PermissionCatalogEntry)
def create_permission(
    body: PermissionCatalogEntry,
    service: Annotated[PermissionMatrixService, Depends(get_permission_matrix_service)],
) -> PermissionCatalogEntry:
    """Create a permission catalog entry."""
    try:
        return service.create_permission(body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/brain/policy-catalog/permissions", response_model=list[PermissionCatalogEntry])
def list_permissions(
    service: Annotated[PermissionMatrixService, Depends(get_permission_matrix_service)],
    category: str | None = None,
    status: str | None = None,
) -> list[PermissionCatalogEntry]:
    """List permission catalog entries."""
    return service.list_permissions(category=category, status=status)


@router.post("/brain/policy-catalog/roles", response_model=RoleTemplate)
def create_role_template(
    body: RoleTemplate,
    service: Annotated[PermissionMatrixService, Depends(get_permission_matrix_service)],
) -> RoleTemplate:
    """Create a role template."""
    try:
        return service.create_role_template(body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/brain/policy-catalog/roles", response_model=list[RoleTemplate])
def list_role_templates(
    service: Annotated[PermissionMatrixService, Depends(get_permission_matrix_service)],
    status: str | None = None,
) -> list[RoleTemplate]:
    """List role templates."""
    return service.list_role_templates(status=status)


@router.post("/brain/policy-catalog/roles/seed-defaults")
def seed_role_defaults(
    body: SeedDefaultsRequest,
    service: Annotated[PermissionMatrixService, Depends(get_permission_matrix_service)],
) -> dict[str, object]:
    """Seed default role templates."""
    return service.seed_default_roles(dry_run=body.dry_run)


@router.post("/brain/policy/simulate", response_model=PolicySimulationResult)
def simulate_policy(
    body: PolicySimulationRequest,
    service: Annotated[PolicySimulationService, Depends(get_policy_simulation_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PolicySimulationResult:
    """Simulate a policy decision without executing the target action."""
    try:
        return service.simulate(body, actor_context)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/brain/policy/tests", response_model=PolicyTestCase)
def create_policy_test(
    body: PolicyTestCase,
    service: Annotated[PolicyTestHarness, Depends(get_policy_test_harness)],
) -> PolicyTestCase:
    """Create a policy test case."""
    try:
        return service.create_test_case(body)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/brain/policy/tests", response_model=list[PolicyTestCase])
def list_policy_tests(
    service: Annotated[PolicyTestHarness, Depends(get_policy_test_harness)],
    status: str | None = None,
    tags: Annotated[list[str] | None, Query()] = None,
) -> list[PolicyTestCase]:
    """List policy test cases."""
    return service.list_test_cases(status=status, tags=tags or [])


@router.post("/brain/policy/tests/run", response_model=PolicyTestRun)
def run_policy_tests(
    body: PolicyTestRunRequest,
    service: Annotated[PolicyTestHarness, Depends(get_policy_test_harness)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PolicyTestRun:
    """Run policy tests."""
    try:
        return service.run_tests(body, actor_context)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/brain/policy/coverage", response_model=PolicyCoverageReport)
def policy_coverage(
    analyzer: Annotated[PolicyCoverageAnalyzer, Depends(get_policy_coverage_analyzer)],
) -> PolicyCoverageReport:
    """Return policy coverage report."""
    try:
        return analyzer.generate()
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.post("/brain/policy/bundles/export", response_model=PolicyBundleRecord)
def export_policy_bundle(
    body: PolicyBundleExportRequest,
    service: Annotated[PolicyBundleService, Depends(get_policy_bundle_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PolicyBundleRecord:
    """Export a policy bundle."""
    request = body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})
    try:
        return service.export_bundle(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/brain/policy/bundles/{policy_bundle_id}", response_model=PolicyBundleRecord)
def get_policy_bundle(
    policy_bundle_id: str,
    service: Annotated[PolicyBundleService, Depends(get_policy_bundle_service)],
) -> PolicyBundleRecord:
    """Return one policy bundle."""
    bundle = service.get_bundle(policy_bundle_id)
    if bundle is None:
        raise HTTPException(status_code=404, detail="policy_bundle_not_found")
    return bundle


@router.get("/brain/policy/bundles", response_model=list[PolicyBundleRecord])
def list_policy_bundles(
    service: Annotated[PolicyBundleService, Depends(get_policy_bundle_service)],
    bundle_type: str | None = None,
) -> list[PolicyBundleRecord]:
    """List policy bundles."""
    return service.list_bundles(bundle_type=bundle_type)


@router.get("/brain/policy/opa/status", response_model=OPAStatus)
def opa_status(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> OPAStatus:
    """Return OPA adapter status."""
    decision = container.policy_adapter.authorize(
        PolicyRequest(
            request_id=f"policy.opa.status-{actor_context.actor_id or 'anonymous'}",
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type="policy.opa.status",
            resource_type="policy_engine",
            resource_id=None,
            risk_level="low",
            approval_present=True,
            requested_permissions=["policy.opa.status"],
            security_scope=actor_context.security_scope or ["workspace:main"],
            context={"actor_context": actor_context.model_dump(mode="json")},
        )
    )
    if not decision.allow:
        raise HTTPException(status_code=403, detail=f"policy_denied:{decision.reason}")
    status = getattr(container.policy_adapter, "status", None)
    if callable(status):
        return cast(OPAStatus, status())
    return OPAStatus(
        available=False,
        url=getattr(container.settings, "opa_url", None),
        policy_loaded=False,
        decision_path="/v1/data/aion/brain/decision",
        reason="policy_adapter_status_unavailable",
        checked_at=datetime.now(UTC),
    )
