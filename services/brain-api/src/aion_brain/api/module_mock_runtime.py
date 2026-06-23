"""Module mock runtime API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from aion_brain.api.kernel import get_kernel_container
from aion_brain.api_support.errors import AIONNotFoundException
from aion_brain.contracts.module_mock_runtime import (
    ModuleMockFinding,
    ModuleMockFindingDismissRequest,
    ModuleMockInvocationCreateRequest,
    ModuleMockOutput,
    ModuleMockProfile,
    ModuleMockProfileCreateRequest,
    ModuleMockProfileSeedRequest,
    ModuleMockQuery,
    ModuleMockQueryResult,
    ModuleMockRun,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.module_mock_runtime.policy import authorize_module_mock_action

router = APIRouter(tags=["module-mock-runtime"])


@router.post("/brain/module-mock/profiles", response_model=ModuleMockProfile)
@router.post("/brain/module-mock-runtime/profiles", response_model=ModuleMockProfile)
def create_mock_profile(
    body: ModuleMockProfileCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleMockProfile:
    """Create deterministic mock profile metadata."""

    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.module_mock_profile_service.create_profile(request)


@router.post("/brain/module-mock/profiles/seed-defaults")
@router.post("/brain/module-mock-runtime/profiles/seed")
def seed_mock_profiles(
    body: ModuleMockProfileSeedRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed or preview default generic mock profiles."""

    request = body.model_copy(
        update={
            "scope": body.scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.module_mock_profile_service.seed_defaults(request)


@router.get("/brain/module-mock/profiles", response_model=list[ModuleMockProfile])
@router.get("/brain/module-mock-runtime/profiles", response_model=list[ModuleMockProfile])
def list_mock_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    profile_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleMockProfile]:
    """List deterministic mock profiles."""

    return container.module_mock_profile_service.list_profiles(
        _scope(scope, actor_context),
        status=status,
        profile_type=profile_type,
        limit=limit,
    )


@router.get(
    "/brain/module-mock/profiles/{mock_profile_id}",
    response_model=ModuleMockProfile,
)
@router.get(
    "/brain/module-mock-runtime/profiles/{mock_profile_id}",
    response_model=ModuleMockProfile,
)
def get_mock_profile(
    mock_profile_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleMockProfile:
    """Return one deterministic mock profile."""

    return container.module_mock_profile_service.get_profile(
        mock_profile_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/module-mock/invoke", response_model=ModuleMockRun)
@router.post("/brain/module-mock-runtime/invocations", response_model=ModuleMockRun)
def invoke_module_mock(
    body: ModuleMockInvocationCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleMockRun:
    """Run a synthetic dry-run module mock invocation."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.module_mock_simulator.invoke(request)


@router.get("/brain/module-mock/runs", response_model=list[ModuleMockRun])
@router.get("/brain/module-mock-runtime/runs", response_model=list[ModuleMockRun])
def list_module_mock_runs(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    capability_binding_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleMockRun]:
    """List module mock dry-run records."""

    return container.module_mock_simulator.list_runs(
        _scope(scope, actor_context),
        status=status,
        capability_binding_id=capability_binding_id,
        limit=limit,
    )


@router.get("/brain/module-mock/runs/{module_mock_run_id}", response_model=ModuleMockRun)
@router.get("/brain/module-mock-runtime/runs/{module_mock_run_id}", response_model=ModuleMockRun)
def get_module_mock_run(
    module_mock_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleMockRun:
    """Return one module mock dry-run record."""

    return container.module_mock_simulator.get_run(
        module_mock_run_id,
        _scope(scope, actor_context),
    )


@router.get(
    "/brain/module-mock/outputs",
    response_model=list[ModuleMockOutput],
)
@router.get(
    "/brain/module-mock-runtime/outputs",
    response_model=list[ModuleMockOutput],
)
def list_module_mock_outputs(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    module_mock_run_id: str | None = None,
    capability_binding_id: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleMockOutput]:
    """List synthetic outputs."""

    resolved_scope = _scope(scope, actor_context)
    authorize_module_mock_action(
        container.policy_adapter,
        "module_mock.output.read",
        resolved_scope,
        actor_id=actor_context.actor_id,
        workspace_id=actor_context.workspace_id,
        trace_id=actor_context.trace_id,
        resource_type="module_mock_output",
        risk_level="low",
    )
    outputs = container.module_mock_repository.list_outputs(
        module_mock_run_id=module_mock_run_id,
        capability_binding_id=capability_binding_id,
        status=status,
        limit=limit,
    )
    if not outputs:
        return []
    runs_by_id = {
        run.module_mock_run_id: run
        for run in container.module_mock_repository.list_runs(limit=limit)
    }
    scoped: list[ModuleMockOutput] = []
    for output in outputs:
        run = runs_by_id.get(output.module_mock_run_id)
        owner_scope = run.owner_scope if run is not None else resolved_scope
        if _in_scope(owner_scope, resolved_scope):
            scoped.append(output)
    return scoped


@router.get(
    "/brain/module-mock/outputs/{module_mock_output_id}",
    response_model=ModuleMockOutput,
)
@router.get(
    "/brain/module-mock-runtime/outputs/{module_mock_output_id}",
    response_model=ModuleMockOutput,
)
def get_module_mock_output(
    module_mock_output_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleMockOutput:
    """Return one synthetic output."""

    resolved_scope = _scope(scope, actor_context)
    authorize_module_mock_action(
        container.policy_adapter,
        "module_mock.output.read",
        resolved_scope,
        actor_id=actor_context.actor_id,
        workspace_id=actor_context.workspace_id,
        trace_id=actor_context.trace_id,
        resource_type="module_mock_output",
        resource_id=module_mock_output_id,
        risk_level="low",
    )
    output = container.module_mock_repository.get_output(module_mock_output_id)
    if output is None:
        raise AIONNotFoundException("module_mock_output_not_found")
    return output


@router.get("/brain/module-mock/findings", response_model=list[ModuleMockFinding])
@router.get("/brain/module-mock-runtime/findings", response_model=list[ModuleMockFinding])
def list_module_mock_findings(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    capability_binding_id: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ModuleMockFinding]:
    """List module mock findings."""

    return container.module_mock_finding_service.list_findings(
        _scope(scope, actor_context),
        status=status,
        severity=severity,
        capability_binding_id=capability_binding_id,
        limit=limit,
    )


@router.post(
    "/brain/module-mock/findings/{module_mock_finding_id}/dismiss",
    response_model=ModuleMockFinding,
)
@router.post(
    "/brain/module-mock-runtime/findings/{module_mock_finding_id}/dismiss",
    response_model=ModuleMockFinding,
)
def dismiss_module_mock_finding(
    module_mock_finding_id: str,
    body: ModuleMockFindingDismissRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ModuleMockFinding:
    """Dismiss a module mock finding without mutating the run."""

    request = body.model_copy(update={"actor_id": body.actor_id or actor_context.actor_id})
    return container.module_mock_finding_service.dismiss_finding(
        module_mock_finding_id,
        _scope(scope, actor_context),
        request,
    )


@router.post("/brain/module-mock/query", response_model=ModuleMockQueryResult)
@router.post("/brain/module-mock-runtime/query", response_model=ModuleMockQueryResult)
def query_module_mock_runtime(
    body: ModuleMockQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ModuleMockQueryResult:
    """Query aggregate module mock runtime records."""

    request = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    return container.module_mock_query_service.query(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope


def _in_scope(owner_scope: list[str], requested_scope: list[str]) -> bool:
    requested = set(requested_scope or [])
    return not requested or bool(set(owner_scope) & requested)


__all__ = ["router"]
