from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_self_model_services() -> None:
    container = kernel_container()

    assert container.self_model_repository is not None
    assert container.self_model_profile_service is not None
    assert container.self_description_service is not None
    assert container.capability_awareness_service is not None
    assert container.limitation_ledger_service is not None
    assert container.confidence_calibrator is not None
    assert container.self_assessment_service is not None
    assert container.introspection_snapshot_service is not None


def test_kernel_diagnostics_include_self_model_checks() -> None:
    diagnostics = kernel_container().diagnostics.run()

    check_names = {check.name for check in diagnostics}

    assert "self_model_enabled" in check_names
    assert "capability_awareness_enabled" in check_names
    assert "active_self_model_present" in check_names
