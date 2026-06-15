"""Performance API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container

SCOPE = ["workspace:main"]


def test_performance_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))
    benchmark = {
        "benchmark_id": "benchmark-api",
        "name": "API benchmark",
        "description": "Generic API benchmark",
        "status": "active",
        "benchmark_type": "smoke",
        "owner_scope": SCOPE,
        "steps": [
            {
                "step_id": "noop",
                "operation_type": "noop",
                "description": "Local no-op",
            }
        ],
        "thresholds": {},
        "metadata": {},
    }

    create = client.post("/brain/performance/benchmarks", json=benchmark)
    listed = client.get("/brain/performance/benchmarks")
    seeded = client.post(
        "/brain/performance/benchmarks/seed-defaults",
        json={"scope": SCOPE, "dry_run": True},
    )
    run = client.post(
        "/brain/performance/benchmarks/run",
        json={"benchmark": benchmark, "owner_scope": SCOPE},
    )

    assert create.status_code == 200
    assert listed.status_code == 200
    assert seeded.json()["benchmark_count"] >= 1
    assert run.status_code == 200
    assert run.json()["status"] == "passed"


def test_baseline_regression_budget_and_summary_apis_work() -> None:
    client = TestClient(create_app(kernel_container()))
    benchmark = {
        "benchmark_id": "benchmark-api-2",
        "name": "API benchmark",
        "description": "Generic API benchmark",
        "status": "active",
        "benchmark_type": "smoke",
        "owner_scope": SCOPE,
        "steps": [
            {
                "step_id": "noop",
                "operation_type": "noop",
                "description": "Local no-op",
            }
        ],
        "thresholds": {},
        "metadata": {},
    }
    run = client.post(
        "/brain/performance/benchmarks/run",
        json={"benchmark": benchmark, "owner_scope": SCOPE},
    ).json()
    baseline = client.post(
        "/brain/performance/baselines/from-runs",
        json={
            "version": "0.1.0",
            "baseline_name": "local",
            "benchmark_run_ids": [run["benchmark_run_id"]],
        },
    ).json()
    regression = client.post(
        "/brain/performance/regression/compare",
        json={
            "benchmark_run_id": run["benchmark_run_id"],
            "baseline_id": baseline["capacity_baseline_id"],
        },
    )
    budget = client.post(
        "/brain/performance/budgets",
        json={
            "resource_budget_profile_id": "budget-api",
            "name": "Local budget",
            "description": "Generic budget",
            "owner_scope": SCOPE,
            "budgets": {"max_request_duration_ms": 1000},
            "enforcement_mode": "report_only",
        },
    )
    summary = client.get("/brain/performance/summary", params={"scope": SCOPE})

    assert regression.status_code == 200
    assert budget.status_code == 200
    assert summary.status_code == 200
    assert summary.json()["sample_count"] >= 1


def test_api_middleware_records_performance_sample_without_body() -> None:
    container = kernel_container()
    client = TestClient(create_app(container))

    client.get("/health")
    samples = container.performance_repository.list_samples(operation_type="api_request")

    assert samples
    assert samples[0].metadata["body_stored"] is False
    assert samples[0].input_size_bytes is None
    assert samples[0].output_size_bytes is None
