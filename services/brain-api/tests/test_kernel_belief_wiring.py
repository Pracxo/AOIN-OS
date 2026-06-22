from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_wires_belief_services() -> None:
    container = kernel_container()

    assert container.belief_repository is not None
    assert container.belief_service is not None
    assert container.belief_support_service is not None
    assert container.belief_contradiction_service is not None
    assert container.belief_query_service is not None
    assert container.truth_maintenance_service is not None
    assert container.claim_extractor is not None


def test_kernel_diagnostics_include_belief_checks() -> None:
    container = kernel_container()

    checks = {check.name: check for check in container.diagnostics.run()}

    assert checks["beliefs_enabled"].status == "passed"
    assert checks["belief_truth_maintenance_enabled"].status == "passed"
    assert checks["belief_claim_extraction_enabled"].status == "passed"
    assert checks["belief_services_present"].status == "passed"
