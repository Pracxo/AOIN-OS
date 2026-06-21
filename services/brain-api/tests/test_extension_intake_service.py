"""Extension intake service tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from tests.extension_helpers import DenyPolicy, extension_intake_request, extension_services


def test_extension_intake_dry_run_does_not_persist_package() -> None:
    services = extension_services()
    intake_service = services["intake_service"]
    repository = services["repository"]

    run = intake_service.intake(extension_intake_request())

    assert run.status == "dry_run"
    assert run.result["metadata_only"] is True
    assert run.result["package_persisted"] is False
    assert repository.list_packages() == []
    fetched = repository.get_intake_run(run.extension_intake_id)
    assert fetched is not None
    assert fetched.extension_intake_id == run.extension_intake_id
    assert fetched.status == run.status


def test_extension_intake_controlled_persists_metadata_and_install_plan() -> None:
    services = extension_services()
    intake_service = services["intake_service"]
    repository = services["repository"]

    run = intake_service.intake(
        extension_intake_request(mode="controlled", create_install_plan=True)
    )

    assert run.status in {"completed", "warning"}
    assert run.extension_package is not None
    assert run.install_plan_created is True
    assert len(repository.list_packages()) == 1
    assert len(
        repository.list_capability_declarations(run.extension_package.extension_package_id)
    ) == 1
    assert len(
        repository.list_dependency_declarations(run.extension_package.extension_package_id)
    ) == 1
    assert len(repository.list_install_plans()) == 1


def test_extension_intake_policy_deny_blocks_metadata_intake() -> None:
    services = extension_services(policy=DenyPolicy())
    intake_service = services["intake_service"]

    with pytest.raises(AIONPolicyDeniedException):
        intake_service.intake(extension_intake_request())
