"""Kernel self-test tests."""

from aion_brain.contracts.kernel import KernelSelfTestRequest
from tests.kernel_fakes import kernel_container


def test_self_test_runs_locally_and_persists_result() -> None:
    container = kernel_container()
    result = container.self_test_service.run(
        KernelSelfTestRequest(scope=["workspace:test"], dry_run=True)
    )
    assert result.status == "passed"
    assert result.report["external_side_effects"] is False
    assert container.self_test_service.get_latest() == result
