"""Capability conformance and readiness API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.conformance import (
    CapabilityTestVector,
    CapabilityTestVectorCreateRequest,
    ConformanceFinding,
    ConformanceProfile,
    ConformanceProfileCreateRequest,
    ConformanceQuery,
    ConformanceQueryResult,
    ConformanceRun,
    ConformanceRunRequest,
)
from aion_brain.contracts.readiness import ReadinessAssessment, ReadinessAssessmentRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer

router = APIRouter(tags=["conformance"])


class DismissFindingRequest(BaseModel):
    """Dismiss a conformance finding without mutating source systems."""

    model_config = ConfigDict(extra="forbid")

    reason: str = Field(min_length=1)


@router.post("/brain/conformance/profiles", response_model=ConformanceProfile)
def create_conformance_profile(
    body: ConformanceProfileCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConformanceProfile:
    """Create a metadata-only conformance profile."""

    request = body.model_copy(
        update={
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.conformance_profile_service.create_profile(request)


@router.post("/brain/conformance/profiles/seed-defaults")
def seed_default_conformance_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    dry_run: bool = True,
) -> dict[str, object]:
    """Seed default generic conformance profiles."""

    return container.conformance_profile_service.seed_default_profiles(
        _scope(scope, actor_context),
        dry_run=dry_run,
    )


@router.get("/brain/conformance/profiles", response_model=list[ConformanceProfile])
def list_conformance_profiles(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    profile_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ConformanceProfile]:
    """List metadata-only conformance profiles."""

    return container.conformance_profile_service.list_profiles(
        _scope(scope, actor_context),
        status=status,
        profile_type=profile_type,
        limit=limit,
    )


@router.get(
    "/brain/conformance/profiles/{conformance_profile_id}",
    response_model=ConformanceProfile,
)
def get_conformance_profile(
    conformance_profile_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConformanceProfile:
    """Return one metadata-only conformance profile."""

    return container.conformance_profile_service.require_profile(
        conformance_profile_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/conformance/test-vectors", response_model=CapabilityTestVector)
def create_capability_test_vector(
    body: CapabilityTestVectorCreateRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CapabilityTestVector:
    """Create a metadata-only capability test vector."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.capability_test_vector_service.create_vector(request)


@router.post(
    "/brain/conformance/test-vectors/generate-for-binding/{capability_binding_id}",
    response_model=list[CapabilityTestVector],
)
def generate_test_vectors_for_binding(
    capability_binding_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> list[CapabilityTestVector]:
    """Generate schema vectors for a binding without invoking it."""

    return container.capability_test_vector_service.generate_schema_vectors_for_binding(
        capability_binding_id,
        _scope(scope, actor_context),
        created_by=actor_context.actor_id,
    )


@router.get("/brain/conformance/test-vectors", response_model=list[CapabilityTestVector])
def list_capability_test_vectors(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    module_slot_id: str | None = None,
    capability_binding_id: str | None = None,
    extension_package_id: str | None = None,
    status: str | None = None,
    vector_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[CapabilityTestVector]:
    """List metadata-only capability test vectors."""

    return container.capability_test_vector_service.list_vectors(
        _scope(scope, actor_context),
        module_slot_id=module_slot_id,
        capability_binding_id=capability_binding_id,
        extension_package_id=extension_package_id,
        status=status,
        vector_type=vector_type,
        limit=limit,
    )


@router.get(
    "/brain/conformance/test-vectors/{test_vector_id}",
    response_model=CapabilityTestVector,
)
def get_capability_test_vector(
    test_vector_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> CapabilityTestVector:
    """Return one metadata-only capability test vector."""

    return container.capability_test_vector_service.require_vector(
        test_vector_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/conformance/run", response_model=ConformanceRun)
def run_conformance(
    body: ConformanceRunRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConformanceRun:
    """Run deterministic metadata-only conformance checks."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.conformance_runner.run(request)


@router.get("/brain/conformance/runs/{conformance_run_id}", response_model=ConformanceRun)
def get_conformance_run(
    conformance_run_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ConformanceRun:
    """Return one conformance run."""

    from aion_brain.api_support.errors import AIONNotFoundException

    run = container.conformance_runner.get_run(conformance_run_id)
    if run is None:
        raise AIONNotFoundException("conformance_run_not_found")
    return run


@router.get("/brain/conformance/findings", response_model=list[ConformanceFinding])
def list_conformance_findings(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    severity: str | None = None,
    finding_type: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ConformanceFinding]:
    """List conformance findings."""

    return container.conformance_finding_service.list_findings(
        _scope(scope, actor_context),
        status=status,
        severity=severity,
        finding_type=finding_type,
        limit=limit,
    )


@router.post(
    "/brain/conformance/findings/{conformance_finding_id}/dismiss",
    response_model=ConformanceFinding,
)
def dismiss_conformance_finding(
    conformance_finding_id: str,
    body: DismissFindingRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ConformanceFinding:
    """Dismiss a conformance finding."""

    return container.conformance_finding_service.dismiss_finding(
        conformance_finding_id,
        _scope(scope, actor_context),
        actor_context.actor_id,
        body.reason,
    )


@router.post("/brain/readiness/assess", response_model=ReadinessAssessment)
def assess_readiness(
    body: ReadinessAssessmentRequest,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReadinessAssessment:
    """Assess extension readiness without activation."""

    request = body.model_copy(
        update={
            "trace_id": body.trace_id or actor_context.trace_id,
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )
    return container.readiness_assessment_service.assess(request)


@router.get(
    "/brain/readiness/assessments",
    response_model=list[ReadinessAssessment],
)
def list_readiness_assessments(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    readiness_level: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[ReadinessAssessment]:
    """List readiness assessments."""

    return container.readiness_assessment_service.list_assessments(
        _scope(scope, actor_context),
        status=status,
        readiness_level=readiness_level,
        limit=limit,
    )


@router.get(
    "/brain/readiness/assessments/{readiness_assessment_id}",
    response_model=ReadinessAssessment,
)
def get_readiness_assessment(
    readiness_assessment_id: str,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReadinessAssessment:
    """Return one readiness assessment."""

    return container.readiness_assessment_service.require_assessment(
        readiness_assessment_id,
        _scope(scope, actor_context),
    )


@router.post("/brain/conformance/query", response_model=ConformanceQueryResult)
def query_conformance(
    body: ConformanceQuery,
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ConformanceQueryResult:
    """Query conformance records."""

    request = body.model_copy(update={"scope": body.scope or actor_context.security_scope})
    return container.conformance_query_service.query(request)


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    return scope or actor_context.security_scope


__all__ = ["router"]
