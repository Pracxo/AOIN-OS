from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_grounding_checks() -> None:
    container = kernel_container()

    checks = {check.name: check.status for check in container.diagnostics.run()}

    assert checks["grounding_enabled"] == "passed"
    assert checks["citation_mapper_enabled"] == "passed"
    assert checks["grounding_services_present"] == "passed"
    assert container.grounding_source_service is not None
    assert container.citation_mapper is not None
