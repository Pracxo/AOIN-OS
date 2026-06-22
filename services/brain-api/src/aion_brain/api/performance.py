"""Local performance benchmark API."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field

from aion_brain.api.kernel import get_kernel_container
from aion_brain.contracts.performance import (
    BenchmarkDefinition,
    BenchmarkRun,
    BenchmarkRunRequest,
    CapacityBaseline,
    PerformanceRegressionReport,
    PerformanceSummary,
    ResourceBudgetProfile,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.kernel.container import KernelContainer
from aion_brain.performance.baseline import CapacityBaselineService
from aion_brain.performance.budgets import ResourceBudgetService
from aion_brain.performance.regression import PerformanceRegressionComparator
from aion_brain.performance.runner import BenchmarkRunner
from aion_brain.performance.summary import PerformanceSummaryService

router = APIRouter(tags=["performance"])


class SeedDefaultsRequest(BaseModel):
    """Default benchmark seeding request."""

    model_config = ConfigDict(extra="forbid")

    scope: list[str] = Field(default_factory=list)
    dry_run: bool = True


class BaselineFromRunsRequest(BaseModel):
    """Capacity baseline creation request."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(min_length=1)
    baseline_name: str = Field(min_length=1)
    benchmark_run_ids: list[str] = Field(default_factory=list)
    created_by: str | None = None


class RegressionCompareRequest(BaseModel):
    """Regression comparison request."""

    model_config = ConfigDict(extra="forbid")

    benchmark_run_id: str = Field(min_length=1)
    baseline_id: str = Field(min_length=1)


def get_benchmark_runner(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> BenchmarkRunner:
    return container.benchmark_runner


def get_capacity_baseline_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> CapacityBaselineService:
    return container.capacity_baseline_service


def get_resource_budget_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> ResourceBudgetService:
    return container.resource_budget_service


def get_performance_regression_comparator(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PerformanceRegressionComparator:
    return container.performance_regression_comparator


def get_performance_summary_service(
    container: Annotated[KernelContainer, Depends(get_kernel_container)],
) -> PerformanceSummaryService:
    return container.performance_summary_service


@router.post("/brain/performance/benchmarks", response_model=BenchmarkDefinition)
def create_benchmark(
    body: BenchmarkDefinition,
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BenchmarkDefinition:
    """Create a local benchmark definition."""
    return service.create_benchmark(
        body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})
    )


@router.get("/brain/performance/benchmarks", response_model=list[BenchmarkDefinition])
def list_benchmarks(
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    status: str | None = None,
    benchmark_type: str | None = None,
) -> list[BenchmarkDefinition]:
    """List local benchmark definitions."""
    return service.list_benchmarks(status=status, benchmark_type=benchmark_type)


@router.get("/brain/performance/benchmarks/{benchmark_id}", response_model=BenchmarkDefinition)
def get_benchmark(
    benchmark_id: str,
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BenchmarkDefinition:
    """Get one benchmark definition."""
    benchmark = service.get_benchmark(benchmark_id, _scope(scope, actor_context))
    if benchmark is None:
        raise HTTPException(status_code=404, detail="benchmark_not_found")
    return benchmark


@router.post("/brain/performance/benchmarks/seed-defaults")
def seed_default_benchmarks(
    body: SeedDefaultsRequest,
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> dict[str, object]:
    """Seed or preview default local benchmarks."""
    return service.seed_defaults(body.scope or actor_context.security_scope, dry_run=body.dry_run)


@router.post("/brain/performance/benchmarks/run", response_model=BenchmarkRun)
def run_benchmark(
    body: BenchmarkRunRequest,
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> BenchmarkRun:
    """Run a deterministic local benchmark."""
    return service.run(_run_request(body, actor_context))


@router.get("/brain/performance/benchmarks/runs/{benchmark_run_id}", response_model=BenchmarkRun)
def get_benchmark_run(
    benchmark_run_id: str,
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> BenchmarkRun:
    """Get one benchmark run."""
    run = service.get_run(benchmark_run_id, _scope(scope, actor_context))
    if run is None:
        raise HTTPException(status_code=404, detail="benchmark_run_not_found")
    return run


@router.get("/brain/performance/benchmarks/runs", response_model=list[BenchmarkRun])
def list_benchmark_runs(
    service: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    benchmark_type: str | None = None,
    limit: int = 50,
) -> list[BenchmarkRun]:
    """List benchmark runs."""
    return service.list_runs(
        _scope(scope, actor_context),
        status=status,
        benchmark_type=benchmark_type,
        limit=limit,
    )


@router.post("/brain/performance/baselines/from-runs", response_model=CapacityBaseline)
def create_capacity_baseline(
    body: BaselineFromRunsRequest,
    service: Annotated[CapacityBaselineService, Depends(get_capacity_baseline_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> CapacityBaseline:
    """Create a local capacity baseline from benchmark runs."""
    return service.create_from_run(
        body.version,
        body.baseline_name,
        body.benchmark_run_ids,
        body.created_by or actor_context.actor_id,
    )


@router.get("/brain/performance/baselines/{capacity_baseline_id}", response_model=CapacityBaseline)
def get_capacity_baseline(
    capacity_baseline_id: str,
    service: Annotated[CapacityBaselineService, Depends(get_capacity_baseline_service)],
) -> CapacityBaseline:
    """Get one capacity baseline."""
    baseline = service.get(capacity_baseline_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="capacity_baseline_not_found")
    return baseline


@router.get("/brain/performance/baselines", response_model=list[CapacityBaseline])
def list_capacity_baselines(
    service: Annotated[CapacityBaselineService, Depends(get_capacity_baseline_service)],
    version: str | None = None,
    status: str | None = None,
) -> list[CapacityBaseline]:
    """List capacity baselines."""
    return service.list(version=version, status=status)


@router.post("/brain/performance/regression/compare", response_model=PerformanceRegressionReport)
def compare_regression(
    body: RegressionCompareRequest,
    runner: Annotated[BenchmarkRunner, Depends(get_benchmark_runner)],
    baselines: Annotated[CapacityBaselineService, Depends(get_capacity_baseline_service)],
    comparator: Annotated[
        PerformanceRegressionComparator,
        Depends(get_performance_regression_comparator),
    ],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> PerformanceRegressionReport:
    """Compare one benchmark run to a baseline."""
    run = runner.get_run(body.benchmark_run_id, actor_context.security_scope)
    baseline = baselines.get(body.baseline_id)
    if run is None:
        raise HTTPException(status_code=404, detail="benchmark_run_not_found")
    if baseline is None:
        raise HTTPException(status_code=404, detail="capacity_baseline_not_found")
    return comparator.compare(run, baseline)


@router.post("/brain/performance/budgets", response_model=ResourceBudgetProfile)
def create_budget_profile(
    body: ResourceBudgetProfile,
    service: Annotated[ResourceBudgetService, Depends(get_resource_budget_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ResourceBudgetProfile:
    """Create a local resource budget profile."""
    return service.create_profile(
        body.model_copy(update={"created_by": body.created_by or actor_context.actor_id})
    )


@router.get("/brain/performance/budgets", response_model=list[ResourceBudgetProfile])
def list_budget_profiles(
    service: Annotated[ResourceBudgetService, Depends(get_resource_budget_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
) -> list[ResourceBudgetProfile]:
    """List local resource budget profiles."""
    return service.list_profiles(_scope(scope, actor_context), status=status)


@router.get("/brain/performance/summary", response_model=PerformanceSummary)
def performance_summary(
    service: Annotated[PerformanceSummaryService, Depends(get_performance_summary_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    operation_type: str | None = None,
    window: str = "latest",
) -> PerformanceSummary:
    """Summarize local performance samples."""
    return service.summarize(
        _scope(scope, actor_context),
        operation_type=operation_type,
        window=window,
    )


def _run_request(body: BenchmarkRunRequest, actor_context: ActorContext) -> BenchmarkRunRequest:
    return body.model_copy(
        update={
            "actor_id": body.actor_id or actor_context.actor_id,
            "workspace_id": body.workspace_id or actor_context.workspace_id,
            "owner_scope": body.owner_scope or actor_context.security_scope,
            "created_by": body.created_by or actor_context.actor_id,
        }
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
