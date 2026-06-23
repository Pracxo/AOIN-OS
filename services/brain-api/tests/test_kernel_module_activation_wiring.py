"""Kernel wiring tests for module activation."""

from tests.kernel_fakes import kernel_container


def test_kernel_container_exposes_module_activation_services() -> None:
    container = kernel_container()

    assert container.module_activation_repository is not None
    assert container.module_activation_request_service is not None
    assert container.activation_blocker_service is not None
    assert container.activation_gate_service is not None
    assert container.activation_review_service is not None
    assert container.activation_plan_service is not None
    assert container.runtime_registration_preview_service is not None
    assert container.module_activation_query_service is not None
