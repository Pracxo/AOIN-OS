from __future__ import annotations

from aion_brain.contracts.operator_console import ConsoleViewModelRequest
from aion_brain.operator_console.service import ConsoleViewModelService
from tests.kernel_fakes import AllowPolicy, FakeTelemetry


def test_view_model_service_returns_unavailable_section_for_missing_service() -> None:
    service = ConsoleViewModelService(
        container=object(),
        policy_adapter=AllowPolicy(),
        telemetry_service=FakeTelemetry(),
    )

    model = service.get_view_model(
        ConsoleViewModelRequest(view="overview", owner_scope=["workspace:main"])
    )

    assert model.read_only is True
    assert model.redaction_applied is True
    assert model.sections
    assert {section.status for section in model.sections} == {"unavailable"}


def test_view_model_service_includes_forbidden_activation_action() -> None:
    service = ConsoleViewModelService(container=object(), policy_adapter=AllowPolicy())

    model = service.get_view_model(
        ConsoleViewModelRequest(view="module_lifecycle", owner_scope=["workspace:main"])
    )

    action_keys = {action.action_key for action in model.forbidden_actions}
    assert "activate_module" in action_keys
    assert "execute_tool" in action_keys


def test_view_model_service_emits_visual_telemetry() -> None:
    telemetry = FakeTelemetry()
    service = ConsoleViewModelService(
        container=object(),
        policy_adapter=AllowPolicy(),
        telemetry_service=telemetry,
    )

    service.get_view_model(ConsoleViewModelRequest(view="overview", owner_scope=["workspace:main"]))

    assert telemetry.events
    assert telemetry.events[0].event_type == "operator_console_view_model_created"
