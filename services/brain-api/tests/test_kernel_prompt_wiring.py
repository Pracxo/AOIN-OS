from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_container_wires_prompt_services() -> None:
    container = kernel_container()

    assert container.prompt_repository is not None
    assert container.prompt_compiler is not None
    assert container.prompt_boundary_checker is not None
    assert container.model_input_manifest_service is not None
    assert container.prompt_preview_service is not None


def test_kernel_diagnostics_include_prompt_checks() -> None:
    names = {check.name for check in kernel_container().diagnostics.run()}

    assert "prompt_compiler_enabled" in names
    assert "prompt_services_present" in names
