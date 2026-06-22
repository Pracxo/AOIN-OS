"""Extension Registry repository tests."""

from __future__ import annotations

from tests.extension_helpers import extension_intake_request, extension_services


def test_extension_repository_persists_package_declarations_and_plan() -> None:
    services = extension_services()
    package_service = services["package_service"]
    capability_service = services["capability_service"]
    dependency_service = services["dependency_service"]
    install_plan_service = services["install_plan_service"]
    repository = services["repository"]

    package = package_service.build_package(extension_intake_request(mode="controlled"))
    saved_package = package_service.save_package(package)
    capabilities = capability_service.persist_declarations(
        saved_package,
        capability_service.from_package(saved_package),
    )
    dependencies = dependency_service.persist_declarations(
        saved_package,
        dependency_service.from_package(saved_package),
    )
    plan = install_plan_service.create_plan(saved_package, scope=["workspace:main"])

    fetched_package = repository.get_package(saved_package.extension_package_id)

    assert fetched_package is not None
    assert fetched_package.extension_package_id == saved_package.extension_package_id
    assert fetched_package.install_plan_id == plan.install_plan_id
    fetched_capabilities = repository.list_capability_declarations(
        saved_package.extension_package_id
    )
    fetched_dependencies = repository.list_dependency_declarations(
        saved_package.extension_package_id
    )
    assert [item.capability_key for item in fetched_capabilities] == [
        item.capability_key for item in capabilities
    ]
    assert [item.dependency_key for item in fetched_dependencies] == [
        item.dependency_key for item in dependencies
    ]
    fetched_plan = repository.get_install_plan(plan.install_plan_id)
    assert fetched_plan is not None
    assert fetched_plan.install_plan_id == plan.install_plan_id
    assert fetched_plan.executable is False
    assert fetched_plan.execution_allowed is False
    assert repository.list_registry_records()[0]["resource_type"] == "extension_package"
