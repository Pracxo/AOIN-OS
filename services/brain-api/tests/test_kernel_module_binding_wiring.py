"""Kernel wiring tests for module bindings."""

from tests.kernel_fakes import kernel_container


def test_kernel_container_exposes_module_binding_services() -> None:
    container = kernel_container()

    assert container.module_binding_repository is not None
    assert container.module_slot_service is not None
    assert container.capability_binding_service is not None
    assert container.binding_validator is not None
    assert container.module_mount_plan_service is not None
    assert container.route_binding_preview_service is not None
    assert container.module_binding_query_service is not None
