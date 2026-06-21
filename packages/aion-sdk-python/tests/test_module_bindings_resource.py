from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_module_bindings_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.module_bindings.create_module_slot({"slot_key": "test.echo"})
    client.module_bindings.get_module_slot("slot-1", scope)
    client.module_bindings.list_module_slots(scope)
    client.module_bindings.archive_module_slot("slot-1", {"reason": "reviewed"}, scope)
    client.module_bindings.delete_module_slot("slot-1", scope)
    client.module_bindings.create_capability_binding({"capability_key": "test.echo"})
    client.module_bindings.get_capability_binding("binding-1", scope)
    client.module_bindings.list_capability_bindings(scope)
    client.module_bindings.disable_capability_binding("binding-1", {"reason": "done"}, scope)
    client.module_bindings.validate({"owner_scope": scope})
    client.module_bindings.get_validation("validation-1", scope)
    client.module_bindings.list_conflicts(scope)
    client.module_bindings.dismiss_conflict("conflict-1", {"reason": "accepted"}, scope)
    client.module_bindings.create_mount_plan({"module_slot_id": "slot-1"})
    client.module_bindings.get_mount_plan("mount-plan-1", scope)
    client.module_bindings.list_mount_plans(scope)
    client.module_bindings.create_route_preview({"capability_binding_id": "binding-1"})
    client.module_bindings.list_route_previews(scope)
    client.module_bindings.query({"scope": scope})

    assert seen == [
        ("POST", "/brain/module-slots"),
        ("GET", "/brain/module-slots/slot-1"),
        ("GET", "/brain/module-slots"),
        ("POST", "/brain/module-slots/slot-1/archive"),
        ("DELETE", "/brain/module-slots/slot-1"),
        ("POST", "/brain/capability-bindings"),
        ("GET", "/brain/capability-bindings/binding-1"),
        ("GET", "/brain/capability-bindings"),
        ("POST", "/brain/capability-bindings/binding-1/disable"),
        ("POST", "/brain/module-bindings/validate"),
        ("GET", "/brain/module-bindings/validations/validation-1"),
        ("GET", "/brain/module-bindings/conflicts"),
        ("POST", "/brain/module-bindings/conflicts/conflict-1/dismiss"),
        ("POST", "/brain/module-bindings/mount-plans"),
        ("GET", "/brain/module-bindings/mount-plans/mount-plan-1"),
        ("GET", "/brain/module-bindings/mount-plans"),
        ("POST", "/brain/module-bindings/route-previews"),
        ("GET", "/brain/module-bindings/route-previews"),
        ("POST", "/brain/module-bindings/query"),
    ]


def test_module_bindings_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.module_bindings as resource

    assert "aion_brain" not in resource.__dict__


def test_module_bindings_resource_brief_aliases_call_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    scope = ["workspace:main"]
    client.module_bindings.create_slot({"slot_key": "test.echo"})
    client.module_bindings.create_binding({"capability_key": "test.echo"})
    client.module_bindings.validate({"owner_scope": scope})
    client.module_bindings.create_mount_plan("slot-1", scope)

    assert seen == [
        ("POST", "/brain/module-slots"),
        ("POST", "/brain/capability-bindings"),
        ("POST", "/brain/module-bindings/validate"),
        ("POST", "/brain/module-bindings/mount-plans"),
    ]
