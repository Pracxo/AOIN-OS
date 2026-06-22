"""Performance summary tests."""

from aion_brain.contracts.performance import PerformanceSample
from tests.performance_fakes import SCOPE, services


def test_performance_summary_service_summarizes_samples() -> None:
    repo, _, _, _, _, summary_service, _ = services()
    repo.save_sample(
        PerformanceSample(
            performance_sample_id="sample-1",
            operation_type="noop",
            component="noop",
            status="passed",
            duration_ms=10,
        )
    )
    repo.save_sample(
        PerformanceSample(
            performance_sample_id="sample-2",
            operation_type="noop",
            component="noop",
            status="failed",
            duration_ms=20,
        )
    )

    summary = summary_service.summarize(SCOPE, operation_type="noop", window="all")

    assert summary.sample_count == 2
    assert summary.error_count == 1
