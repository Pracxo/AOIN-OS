"""Kernel wiring tests for notification center."""

from __future__ import annotations

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_kernel_registers_notification_services_and_routes() -> None:
    container = kernel_container()
    names = {record.service_name for record in container.service_registry.list_services()}
    checks = {check.name: check.status for check in container.diagnostics.run()}
    exported = container.contract_export_service.export_contracts(create_app(container))

    assert "notification_router" in names
    assert "alert_service" in names
    assert "escalation_service" in names
    assert "notification_digest_service" in names
    assert checks["notification_router_present"] == "passed"
    assert checks["external_notifications_enabled"] == "passed"
    assert checks["notification_local_delivery_only"] == "passed"
    assert "/brain/notifications/publish" in exported.openapi["paths"]
    assert "/brain/alerts" in exported.openapi["paths"]
    assert "NotificationRecord" in exported.contracts
    assert "AlertRecord" in exported.contracts
