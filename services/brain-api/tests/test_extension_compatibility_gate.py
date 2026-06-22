"""Extension compatibility gate tests."""

from __future__ import annotations

from aion_brain.config import Settings
from aion_brain.contracts.extension_compatibility import ExtensionCompatibilityRequest
from tests.extension_helpers import extension_intake_request, extension_services


def test_extension_compatibility_gate_passes_generic_metadata() -> None:
    services = extension_services()
    package_service = services["package_service"]
    compatibility_gate = services["compatibility_gate"]
    package = package_service.save_package(
        package_service.build_package(extension_intake_request(mode="controlled"))
    )

    run = compatibility_gate.check(
        ExtensionCompatibilityRequest(
            extension_package_id=package.extension_package_id,
            owner_scope=["workspace:main"],
        )
    )

    assert run.status == "warning"
    assert run.result["metadata_only"] is True


def test_extension_compatibility_gate_blocks_unsafe_runtime_flags() -> None:
    settings = Settings(_env_file=None, AION_EXTENSION_CODE_LOADING_ENABLED=True)
    services = extension_services(settings=settings)
    package_service = services["package_service"]
    compatibility_gate = services["compatibility_gate"]
    package = package_service.save_package(
        package_service.build_package(extension_intake_request(mode="controlled"))
    )

    run = compatibility_gate.check(
        ExtensionCompatibilityRequest(
            extension_package_id=package.extension_package_id,
            owner_scope=["workspace:main"],
        )
    )

    assert run.status == "blocked"
    assert any(item["code"] == "unsafe_extension_settings" for item in run.blockers)
