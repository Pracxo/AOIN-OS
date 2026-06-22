"""Extension Registry contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.extensions import ExtensionInstallPlan, ExtensionManifest
from tests.extension_helpers import extension_manifest


def test_extension_manifest_accepts_generic_metadata() -> None:
    manifest = extension_manifest()

    assert manifest.extension_key == "test.echo"
    assert manifest.package_type == "module"
    assert manifest.declared_capabilities[0]["capability_key"] == "test.echo.respond"


def test_extension_manifest_rejects_executable_payloads() -> None:
    with pytest.raises(ValidationError):
        extension_manifest(metadata={"script": "print('no')"})


def test_extension_manifest_rejects_domain_terms() -> None:
    with pytest.raises(ValidationError):
        ExtensionManifest.model_validate(
            {
                **extension_manifest().model_dump(mode="python"),
                "extension_key": "test.finance",
            }
        )


def test_extension_install_plan_cannot_be_executable() -> None:
    with pytest.raises(ValidationError):
        ExtensionInstallPlan(
            install_plan_id="plan-1",
            extension_package_id="package-1",
            status="planned",
            plan_type="future_install",
            owner_scope=["workspace:main"],
            blocked=False,
            executable=True,
            execution_allowed=False,
            created_at=datetime.now(UTC),
        )
