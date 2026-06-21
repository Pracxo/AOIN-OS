from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_extensions_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.extensions.validate_manifest({"extension_key": "test.echo"})
    client.extensions.intake({"owner_scope": ["workspace:main"]})
    client.extensions.get_intake_run("intake-1", ["workspace:main"])
    client.extensions.get_package("package-1", ["workspace:main"])
    client.extensions.query({"scope": ["workspace:main"]})
    client.extensions.archive_package(
        "package-1",
        {"reason": "done"},
        ["workspace:main"],
    )
    client.extensions.delete_package("package-1", ["workspace:main"])
    client.extensions.list_capabilities("package-1", ["workspace:main"])
    client.extensions.list_dependencies("package-1", ["workspace:main"])
    client.extensions.check_compatibility({"extension_package_id": "package-1"})
    client.extensions.get_compatibility("compat-1", ["workspace:main"])
    client.extensions.review_package(
        "package-1",
        {"decision": "approve", "reason": "metadata reviewed"},
        ["workspace:main"],
    )
    client.extensions.list_reviews(["workspace:main"])
    client.extensions.create_install_plan("package-1", {"scope": ["workspace:main"]})
    client.extensions.get_install_plan("plan-1", ["workspace:main"])
    client.extensions.list_install_plans(["workspace:main"])

    assert seen == [
        ("POST", "/brain/extensions/manifests/validate"),
        ("POST", "/brain/extensions/intake"),
        ("GET", "/brain/extensions/intake-runs/intake-1"),
        ("GET", "/brain/extensions/packages/package-1"),
        ("POST", "/brain/extensions/query"),
        ("POST", "/brain/extensions/packages/package-1/archive"),
        ("DELETE", "/brain/extensions/packages/package-1"),
        ("GET", "/brain/extensions/packages/package-1/capabilities"),
        ("GET", "/brain/extensions/packages/package-1/dependencies"),
        ("POST", "/brain/extensions/compatibility/check"),
        ("GET", "/brain/extensions/compatibility/compat-1"),
        ("POST", "/brain/extensions/packages/package-1/review"),
        ("GET", "/brain/extensions/reviews"),
        ("POST", "/brain/extensions/packages/package-1/install-plan"),
        ("GET", "/brain/extensions/install-plans/plan-1"),
        ("GET", "/brain/extensions/install-plans"),
    ]


def test_extensions_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.extensions as resource

    assert "aion_brain" not in resource.__dict__
