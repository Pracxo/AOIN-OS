"""Default local benchmark definitions."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from aion_brain.contracts.performance import BenchmarkDefinition, BenchmarkStep


def build_smoke_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build a fast local smoke benchmark."""
    return _definition(
        "smoke",
        "Local smoke benchmark",
        "Checks core local readiness with side-effect-safe operations.",
        scope,
        [
            _step("health", "health", "Read health state."),
            _step("kernel_status", "kernel_status", "Read kernel status."),
            _step("noop", "noop", "Run a local no-op timing sample."),
        ],
    )


def build_api_latency_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build a local API latency benchmark definition."""
    return _definition(
        "api_latency",
        "Local API latency benchmark",
        "Measures local request-style operations without request bodies.",
        scope,
        [
            _step("health", "health", "Time health route."),
            _step("kernel_status", "kernel_status", "Time status route."),
        ],
    )


def build_memory_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build a memory benchmark definition."""
    return _definition(
        "memory",
        "Local memory benchmark",
        "Measures generic memory write and recall paths.",
        scope,
        [
            _step("memory_create", "memory_create", "Create generic memory candidate."),
            _step("memory_retrieve", "memory_retrieve", "Retrieve generic memory candidate."),
        ],
    )


def build_retrieval_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build a retrieval benchmark definition."""
    return _definition(
        "retrieval",
        "Local retrieval benchmark",
        "Measures generic retrieval and context assembly paths.",
        scope,
        [
            _step("retrieval_query", "retrieval_query", "Run generic retrieval query."),
            _step("context_compile", "context_compile", "Compile generic context."),
        ],
    )


def build_reasoning_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build a deterministic reasoning benchmark definition."""
    return _definition(
        "reasoning",
        "Local reasoning benchmark",
        "Measures deterministic reasoning and planning paths.",
        scope,
        [
            _step(
                "reasoning_deterministic",
                "reasoning_deterministic",
                "Run deterministic reasoning.",
            ),
            _step("planning", "planning", "Create deterministic plan."),
            _step("brain_think", "brain_think", "Run deterministic Brain loop."),
        ],
    )


def build_visual_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build a visual projection benchmark definition."""
    return _definition(
        "visual",
        "Local visual projection benchmark",
        "Measures local Brain Map construction.",
        scope,
        [_step("visual_map", "visual_map", "Build compact Brain Map.")],
    )


def build_full_local_benchmark(scope: list[str]) -> BenchmarkDefinition:
    """Build the broad local benchmark suite."""
    return _definition(
        "full_local",
        "Full local benchmark",
        "Measures deterministic local Brain operations without external providers.",
        scope,
        [
            _step("health", "health", "Read health state."),
            _step("kernel_status", "kernel_status", "Read kernel status."),
            _step("event_ingest", "event_ingest", "Ingest generic event in dry-run mode."),
            _step("memory_create", "memory_create", "Create generic memory candidate."),
            _step("memory_retrieve", "memory_retrieve", "Retrieve generic memory candidate."),
            _step("evidence_ingest", "evidence_ingest", "Ingest generic evidence in dry-run mode."),
            _step("evidence_search", "evidence_search", "Search generic evidence."),
            _step("retrieval_query", "retrieval_query", "Run generic retrieval query."),
            _step("context_compile", "context_compile", "Compile generic context."),
            _step("reasoning_deterministic", "reasoning_deterministic", "Run local reasoner."),
            _step("planning", "planning", "Create deterministic plan."),
            _step("brain_think", "brain_think", "Run deterministic Brain loop."),
            _step("command_noop", "command_noop", "Process command no-op."),
            _step("event_dispatch_dry_run", "event_dispatch_dry_run", "Dry-run event dispatch."),
            _step("workflow_dry_run", "workflow_dry_run", "Dry-run workflow path."),
            _step("cycle_dry_run", "cycle_dry_run", "Dry-run cycle path."),
            _step("visual_map", "visual_map", "Build compact Brain Map."),
            _step("backup_dry_run", "backup_dry_run", "Run backup dry-run path."),
            _step(
                "release_baseline_dry_run",
                "release_baseline_dry_run",
                "Run release baseline dry-run path.",
                required=False,
            ),
        ],
    )


def list_default_benchmarks(scope: list[str]) -> list[BenchmarkDefinition]:
    """Return all default benchmark definitions."""
    return [
        build_smoke_benchmark(scope),
        build_api_latency_benchmark(scope),
        build_memory_benchmark(scope),
        build_retrieval_benchmark(scope),
        build_reasoning_benchmark(scope),
        build_visual_benchmark(scope),
        build_full_local_benchmark(scope),
    ]


def _definition(
    benchmark_type: str,
    name: str,
    description: str,
    scope: list[str],
    steps: list[BenchmarkStep],
) -> BenchmarkDefinition:
    benchmark_id = f"benchmark-{uuid5(NAMESPACE_URL, f'aion:{benchmark_type}').hex}"
    now = datetime.now(UTC)
    return BenchmarkDefinition(
        benchmark_id=benchmark_id,
        name=name,
        description=description,
        benchmark_type=benchmark_type,  # type: ignore[arg-type]
        owner_scope=scope,
        steps=steps,
        thresholds={"default_threshold_ms": 1000},
        metadata={"local_only": True, "external_calls": False},
        created_at=now,
        updated_at=now,
    )


def _step(
    step_id: str,
    operation_type: str,
    description: str,
    *,
    required: bool = True,
) -> BenchmarkStep:
    return BenchmarkStep(
        step_id=step_id,
        operation_type=operation_type,  # type: ignore[arg-type]
        description=description,
        threshold_ms=1000,
        required=required,
        metadata={"local_only": True},
    )
