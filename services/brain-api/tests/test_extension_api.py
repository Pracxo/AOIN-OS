"""Extension Registry API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.extension_helpers import extension_manifest
from tests.kernel_fakes import kernel_container


def test_extension_registry_api_routes_work() -> None:
    client = TestClient(create_app(kernel_container()))
    manifest = extension_manifest(
        declared_dependencies=[],
        declared_policy_actions=[],
    ).model_dump(mode="json")

    validation = client.post("/brain/extensions/manifests/validate", json=manifest)
    dry_run = client.post(
        "/brain/extensions/intake",
        json={"owner_scope": ["workspace:main"], "manifest": manifest},
    )
    controlled = client.post(
        "/brain/extensions/intake",
        json={
            "mode": "controlled",
            "owner_scope": ["workspace:main"],
            "manifest": manifest,
            "create_install_plan": True,
        },
    )

    assert validation.status_code == 200
    assert dry_run.status_code == 200
    assert dry_run.json()["result"]["package_persisted"] is False
    assert controlled.status_code == 200
    package = controlled.json()["extension_package"]
    package_id = package["extension_package_id"]
    intake_id = controlled.json()["extension_intake_id"]
    created_plan = client.post(
        f"/brain/extensions/packages/{package_id}/install-plan",
        json={"scope": ["workspace:main"]},
    )
    install_plan_id = created_plan.json()["install_plan_id"]

    responses = [
        client.get(
            f"/brain/extensions/intake-runs/{intake_id}",
            params={"scope": "workspace:main"},
        ),
        client.get(
            f"/brain/extensions/packages/{package_id}",
            params={"scope": "workspace:main"},
        ),
        client.post("/brain/extensions/query", json={"scope": ["workspace:main"]}),
        client.get(
            f"/brain/extensions/packages/{package_id}/capabilities",
            params={"scope": "workspace:main"},
        ),
        client.get(
            f"/brain/extensions/packages/{package_id}/dependencies",
            params={"scope": "workspace:main"},
        ),
        client.post(
            "/brain/extensions/compatibility/check",
            json={"extension_package_id": package_id, "owner_scope": ["workspace:main"]},
        ),
        client.post(
            f"/brain/extensions/packages/{package_id}/review",
            params={"scope": "workspace:main"},
            json={
                "extension_package_id": package_id,
                "decision": "approve",
                "reason": "metadata reviewed",
            },
        ),
        client.get("/brain/extensions/reviews", params={"scope": "workspace:main"}),
        created_plan,
        client.get(
            f"/brain/extensions/install-plans/{install_plan_id}",
            params={"scope": "workspace:main"},
        ),
        client.get("/brain/extensions/install-plans", params={"scope": "workspace:main"}),
        client.post(
            f"/brain/extensions/packages/{package_id}/archive",
            params={"scope": "workspace:main"},
            json={"reason": "metadata cleanup"},
        ),
        client.delete(
            f"/brain/extensions/packages/{package_id}",
            params={"scope": "workspace:main"},
        ),
    ]

    assert all(response.status_code == 200 for response in responses)
    assert responses[2].json()["total_count"] >= 1
    assert responses[-1].json()["deleted"] is True
