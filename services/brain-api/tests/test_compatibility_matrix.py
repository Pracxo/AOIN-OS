"""Compatibility matrix tests."""

from __future__ import annotations

from aion_brain.versioning import compatibility
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


def test_sdk_compatibility_discovers_resources_from_repo_path_without_import(
    tmp_path,
    monkeypatch,
) -> None:  # type: ignore[no-untyped-def]
    resource_dir = tmp_path / "packages/aion-sdk-python/src/aion_sdk/resources"
    resource_dir.mkdir(parents=True)
    for name in compatibility.SDK_REQUIRED_RESOURCES:
        (resource_dir / f"{name}.py").write_text('"""resource."""\n', encoding="utf-8")

    def raise_missing(_name: str) -> object:
        raise ModuleNotFoundError("aion_sdk")

    monkeypatch.setattr(compatibility, "find_spec", raise_missing)
    service = SDKCompatibilityService(
        AllowPolicy(),
        settings=settings(),
        root_dir=tmp_path,
    )

    report = service.check(SCOPE)

    assert report.compatible is True
    assert report.missing_endpoints == []
