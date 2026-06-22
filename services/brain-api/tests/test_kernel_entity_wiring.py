from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_wires_concept_and_entity_services() -> None:
    container = kernel_container()

    assert container.concept_service is not None
    assert container.entity_service is not None
    assert container.entity_query_service is not None
    assert container.entity_alias_service is not None
    assert container.reference_link_service is not None
    assert container.entity_resolver is not None
    assert container.entity_merge_service is not None
    assert container.entity_split_service is not None


def test_kernel_diagnostics_include_entity_checks() -> None:
    container = kernel_container()

    checks = {check.name: check for check in container.diagnostics.run()}

    assert checks["concepts_enabled"].status == "passed"
    assert checks["entities_enabled"].status == "passed"
    assert checks["entity_resolution_enabled"].status == "passed"
    assert checks["entity_auto_merge_disabled"].status == "passed"
    assert checks["entity_services_present"].status == "passed"
