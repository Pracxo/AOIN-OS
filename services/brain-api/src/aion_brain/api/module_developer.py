"""Module Developer Kit API."""

from datetime import UTC, datetime
from typing import Annotated, cast
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.contracts.module_developer import (
    ModuleCertificationRequest,
    ModuleCertificationRun,
    ModuleCompatibilityReport,
    ModulePackage,
    ModulePackageCreateRequest,
    ModuleScaffold,
    ModuleScaffoldRequest,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.contracts.telemetry import (
    VisualNodeType,
    VisualTelemetryEvent,
    VisualTelemetryEventType,
)
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.module_developer.certifier import ModuleCertifier
from aion_brain.module_developer.compatibility import ModuleCompatibilityChecker
from aion_brain.module_developer.contract_tests import ModuleContractTestHarness
from aion_brain.module_developer.scaffold import ModuleScaffoldGenerator

router = APIRouter(prefix="/brain/module-developer", tags=["module-developer"])


class DisableModulePackageRequest(BaseModel):
    """Disable package request."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    reason: str = Field(min_length=1)


class ContractTestRunRequest(BaseModel):
    """Contract test run request."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = True


def get_kernel_container(request: Request) -> KernelContainer:
    """Return the kernel container."""

    container = getattr(request.app.state, "kernel_container", None)
    if not isinstance(container, KernelContainer):
        raise RuntimeError("AION kernel container is not configured")
    return container


def get_module_certifier(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ModuleCertifier:
    """Return module certifier."""

    return container.module_certifier


def get_module_scaffold_generator(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ModuleScaffoldGenerator:
    """Return module scaffold generator."""

    return container.module_scaffold_generator


def get_module_compatibility_checker(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ModuleCompatibilityChecker:
    """Return compatibility checker."""

    return container.module_compatibility_checker


def get_module_contract_test_harness(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ModuleContractTestHarness:
    """Return contract test harness."""

    return container.module_contract_test_harness


@router.post("/packages", response_model=ModulePackage)
def submit_package(
    body: ModulePackageCreateRequest,
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModulePackage:
    """Submit a module package contract."""

    request = body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})
    try:
        return certifier.submit_package(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@router.get("/packages", response_model=list[ModulePackage])
def list_packages(
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    status: str | None = None,
    module_id: str | None = None,
) -> list[ModulePackage]:
    """List module packages."""

    _authorize(container, actor_context, "module.package.read", "low")
    return certifier.list_packages(status=status, module_id=module_id)


@router.get("/packages/{module_package_id}", response_model=ModulePackage)
def get_package(
    module_package_id: str,
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModulePackage:
    """Return one module package."""

    _authorize(container, actor_context, "module.package.read", "low")
    package = certifier.get_package(module_package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="module_package_not_found")
    return package


@router.post("/packages/{module_package_id}/disable", response_model=ModulePackage)
def disable_package(
    module_package_id: str,
    body: DisableModulePackageRequest,
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModulePackage:
    """Disable one module package."""

    try:
        return certifier.disable_package(
            module_package_id,
            body.actor_id or actor_context.actor_id,
            body.reason,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/packages/{module_package_id}/certify", response_model=ModuleCertificationRun)
def certify_package(
    module_package_id: str,
    body: ModuleCertificationRequest,
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleCertificationRun:
    """Certify one module package."""

    request = body.model_copy(
        update={
            "module_package_id": module_package_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
        }
    )
    try:
        return certifier.certify(request)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/certifications/{certification_run_id}", response_model=ModuleCertificationRun)
def get_certification_run(
    certification_run_id: str,
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleCertificationRun:
    """Return one certification run."""

    _authorize(container, actor_context, "module.package.read", "low")
    run = certifier.get_certification_run(certification_run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="certification_run_not_found")
    return run


@router.get("/certifications", response_model=list[ModuleCertificationRun])
def list_certification_runs(
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    module_package_id: str | None = None,
) -> list[ModuleCertificationRun]:
    """List certification runs."""

    _authorize(container, actor_context, "module.package.read", "low")
    return certifier.list_certification_runs(module_package_id)


@router.post("/scaffold", response_model=ModuleScaffold)
def scaffold_module(
    body: ModuleScaffoldRequest,
    generator: Annotated[ModuleScaffoldGenerator, Depends(get_module_scaffold_generator)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleScaffold:
    """Generate static generic module package files."""

    _authorize(container, actor_context, "module.scaffold.create", "low")
    request = body.model_copy(
        update={"owner_scope": body.owner_scope or actor_context.security_scope}
    )
    scaffold = generator.scaffold(request)
    _emit_telemetry(
        container,
        "module_scaffold_created",
        "scaffold",
        scaffold.module_id,
        0.4,
        {"package_name": scaffold.package_name},
    )
    return scaffold


@router.post(
    "/packages/{module_package_id}/compatibility",
    response_model=ModuleCompatibilityReport,
)
def check_compatibility(
    module_package_id: str,
    certifier: Annotated[ModuleCertifier, Depends(get_module_certifier)],
    checker: Annotated[ModuleCompatibilityChecker, Depends(get_module_compatibility_checker)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleCompatibilityReport:
    """Check module package compatibility."""

    _authorize(container, actor_context, "module.compatibility.check", "low")
    package = certifier.get_package(module_package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="module_package_not_found")
    report = checker.check(package)
    _emit_telemetry(
        container,
        "module_compatibility_checked",
        "compatibility",
        report.report_id,
        0.5,
        {"compatible": report.compatible, "module_package_id": package.module_package_id},
        edge_from=package.module_package_id,
    )
    return report


@router.post(
    "/packages/{module_package_id}/contract-tests/run",
    response_model=ModuleCertificationRun,
)
def run_contract_tests(
    module_package_id: str,
    body: ContractTestRunRequest,
    harness: Annotated[ModuleContractTestHarness, Depends(get_module_contract_test_harness)],
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleCertificationRun:
    """Run static dry-run contract tests."""

    _authorize(container, actor_context, "module.contract_test.run", "low")
    run = harness.run_tests(module_package_id, dry_run=body.dry_run)
    _emit_telemetry(
        container,
        "module_contract_test_run",
        "contract_test",
        run.certification_run_id,
        0.6,
        {"status": run.status},
        edge_from=module_package_id,
    )
    return run


def _authorize(
    container: KernelContainer,
    actor_context: ActorContext,
    action_type: str,
    risk_level: str,
) -> None:
    """Authorize module developer API actions."""

    decision = container.policy_adapter.authorize(
        PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=actor_context.trace_id,
            actor_id=actor_context.actor_id,
            workspace_id=actor_context.workspace_id,
            action_type=action_type,
            resource_type="module_package",
            resource_id=None,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=actor_context.security_scope or ["workspace:main"],
            context={"actor_context": actor_context.model_dump(mode="json")},
        )
    )
    if not decision.allow:
        raise HTTPException(status_code=403, detail=decision.reason)


def _emit_telemetry(
    container: KernelContainer,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, object],
    *,
    edge_from: str | None = None,
) -> None:
    emit = getattr(container.telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                trace_id=node_id,
                event_type=cast(VisualTelemetryEventType, event_type),
                node_type=cast(VisualNodeType, node_type),
                node_id=node_id,
                edge_from=edge_from,
                edge_to=node_id,
                intensity=intensity,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
