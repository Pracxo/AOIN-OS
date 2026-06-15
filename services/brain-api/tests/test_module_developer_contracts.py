"""Module developer contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.module_developer import (
    CapabilityCertification,
    ModulePackage,
    ModuleScaffoldRequest,
)
from tests.module_developer_fakes import package


def test_module_package_validates_status() -> None:
    with pytest.raises(ValidationError):
        ModulePackage.model_validate({**package().model_dump(mode="python"), "status": "bad"})


def test_module_package_rejects_domain_specific_prefix() -> None:
    with pytest.raises(ValidationError):
        ModulePackage.model_validate(
            {
                **package().model_dump(mode="python"),
                "module_id": "finance.alpha",
            }
        )


def test_module_package_rejects_secret_like_metadata() -> None:
    with pytest.raises(ValidationError):
        ModulePackage.model_validate(
            {
                **package().model_dump(mode="python"),
                "metadata": {"api_key": "nope"},
            }
        )


def test_module_scaffold_request_rejects_empty_owner_scope() -> None:
    with pytest.raises(ValidationError):
        ModuleScaffoldRequest(
            module_id="generic.example",
            package_name="generic-example",
            owner_scope=[],
        )


def test_capability_certification_validates_score_bounds() -> None:
    with pytest.raises(ValidationError):
        CapabilityCertification(
            certification_id="cert-1",
            module_package_id="pkg-1",
            module_id="generic.example",
            version="0.1.0",
            capability_id="generic.example.echo",
            status="passed",
            score=2.0,
            checks=[],
            failures=[],
            warnings=[],
        )

