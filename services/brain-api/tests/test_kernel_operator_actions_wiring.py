from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_operator_action_checks() -> None:
    container = kernel_container()
    names = {check.name for check in container.diagnostics.run()}

    assert "operator_actions_enabled" in names
    assert "operator_action_previews_enabled" in names
    assert "operator_action_reviews_enabled" in names
    assert "operator_action_execution_enabled" in names
    assert "operator_action_external_calls_enabled" in names
    assert "operator_action_activation_enabled" in names
    assert "operator_action_services_present" in names
    assert hasattr(container, "operator_action_request_service")
    assert hasattr(container, "operator_action_preview_service")
    assert hasattr(container, "operator_action_review_service")
