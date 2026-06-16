from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_wires_learning_synthesis_services() -> None:
    container = kernel_container()

    assert container.learning_synthesis_repository is not None
    assert container.experience_service is not None
    assert container.pattern_miner is not None
    assert container.lesson_service is not None
    assert container.learning_synthesizer is not None
    assert container.skill_suggestion_service is not None
    assert container.regression_suggestion_service is not None
    assert container.learning_query_service is not None


def test_kernel_diagnostics_include_learning_checks() -> None:
    diagnostics = kernel_container().diagnostics.run()

    check_names = {check.name for check in diagnostics}

    assert "learning_synthesis_enabled" in check_names
    assert "learning_services_present" in check_names
