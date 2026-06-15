"""Module compatibility tests."""

from aion_brain.config import Settings
from aion_brain.module_developer.compatibility import ModuleCompatibilityChecker
from tests.module_developer_fakes import package


def test_compatibility_checker_passes_generic_package() -> None:
    report = ModuleCompatibilityChecker(Settings(_env_file=None)).check(package())

    assert report.compatible is True
    assert report.issues == []


def test_compatibility_checker_warns_unsupported_execution_mode() -> None:
    bad = package(manifest=package().manifest.model_copy(update={"execution_mode": "external"}))

    report = ModuleCompatibilityChecker(Settings(_env_file=None)).check(bad)

    assert any(warning["code"] == "unsupported_execution_mode" for warning in report.warnings)

