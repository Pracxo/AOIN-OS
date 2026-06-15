"""Module developer API tests."""

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container
from tests.module_developer_fakes import package_request


def test_module_developer_api_package_submit_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/module-developer/packages",
        json=package_request().model_dump(mode="json"),
    )

    assert response.status_code == 200
    assert response.json()["module_id"] == "generic.example"


def test_module_developer_api_package_certify_works() -> None:
    client = TestClient(create_app(kernel_container()))
    package_response = client.post(
        "/brain/module-developer/packages",
        json=package_request().model_dump(mode="json"),
    )
    package_id = package_response.json()["module_package_id"]

    response = client.post(
        f"/brain/module-developer/packages/{package_id}/certify",
        json={"module_package_id": package_id, "owner_scope": ["workspace:main"]},
    )

    assert response.status_code == 200
    assert response.json()["module_package_id"] == package_id


def test_module_developer_api_scaffold_works() -> None:
    client = TestClient(create_app(kernel_container()))

    response = client.post(
        "/brain/module-developer/scaffold",
        json={
            "module_id": "generic.example",
            "package_name": "generic-example",
            "owner_scope": ["workspace:main"],
        },
    )

    assert response.status_code == 200
    assert "aion.module.yaml" in response.json()["files"]


def test_module_developer_api_compatibility_works() -> None:
    client = TestClient(create_app(kernel_container()))
    package_response = client.post(
        "/brain/module-developer/packages",
        json=package_request().model_dump(mode="json"),
    )
    package_id = package_response.json()["module_package_id"]

    response = client.post(f"/brain/module-developer/packages/{package_id}/compatibility")

    assert response.status_code == 200
    assert response.json()["module_id"] == "generic.example"


def test_module_developer_api_contract_test_run_works() -> None:
    client = TestClient(create_app(kernel_container()))
    package_response = client.post(
        "/brain/module-developer/packages",
        json=package_request().model_dump(mode="json"),
    )
    package_id = package_response.json()["module_package_id"]

    response = client.post(
        f"/brain/module-developer/packages/{package_id}/contract-tests/run",
        json={"dry_run": True},
    )

    assert response.status_code == 200
    assert response.json()["report"]["module_code_executed"] is False

