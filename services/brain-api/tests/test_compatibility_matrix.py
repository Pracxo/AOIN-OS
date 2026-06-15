"""Compatibility matrix tests."""

from __future__ import annotations

from aion_brain.versioning.compatibility import CompatibilityMatrixService, SDKCompatibilityService
from tests.versioning_fakes import SCOPE, AllowPolicy, repository, settings


def test_compatibility_matrix_marks_unavailable_optional_adapters_as_warning() -> None:
    service = CompatibilityMatrixService(repository(), AllowPolicy(), settings=settings())

    matrix = service.generate("0.1.0", SCOPE)

    assert matrix.status == "warning"
    assert matrix.optional_adapters["turbovec"]["required"] is False


def test_sdk_compatibility_passes_when_required_resources_available() -> None:
    service = SDKCompatibilityService(
        AllowPolicy(),
        settings=settings(),
        sdk_resource_names=[
            "health",
            "kernel",
            "events",
            "memory",
            "commands",
            "scenarios",
            "versioning",
        ],
    )

    report = service.check(SCOPE)

    assert report.compatible is True
    assert report.missing_endpoints == []


def test_sdk_compatibility_reports_missing_resource() -> None:
    service = SDKCompatibilityService(
        AllowPolicy(),
        settings=settings(),
        sdk_resource_names=["health"],
    )

    report = service.check(SCOPE)

    assert report.compatible is False
    assert "versioning" in report.missing_endpoints
