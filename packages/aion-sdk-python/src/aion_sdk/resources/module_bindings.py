"""Module binding registry SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ModuleBindingsResource:
    """Client helpers for metadata-only module binding APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_module_slot(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-slots", json=payload)

    def create_slot(self, payload: JSONDict) -> JSONValue:
        return self.create_module_slot(payload)

    def get_module_slot(self, module_slot_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-slots/{module_slot_id}",
            params={"scope": list(scope)},
        )

    def get_slot(self, module_slot_id: str, scope: Sequence[str]) -> JSONValue:
        return self.get_module_slot(module_slot_id, scope)

    def list_module_slots(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        slot_type: str | None = None,
        extension_package_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {
            "scope": list(scope),
            "include_deleted": include_deleted,
            "limit": limit,
        }
        _set(params, "status", status)
        _set(params, "slot_type", slot_type)
        _set(params, "extension_package_id", extension_package_id)
        return self._client.get("/brain/module-slots", params=params)

    def list_slots(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        slot_type: str | None = None,
        extension_package_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self.list_module_slots(
            scope,
            status=status,
            slot_type=slot_type,
            extension_package_id=extension_package_id,
            limit=limit,
        )

    def archive_module_slot(
        self,
        module_slot_id: str,
        payload: JSONDict,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-slots/{module_slot_id}/archive",
            json=payload,
            params={"scope": list(scope)},
        )

    def archive_slot(
        self,
        module_slot_id: str,
        reason: str,
        scope: Sequence[str] = (),
    ) -> JSONValue:
        return self.archive_module_slot(module_slot_id, {"reason": reason}, scope)

    def delete_module_slot(self, module_slot_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.delete(
            f"/brain/module-slots/{module_slot_id}",
            params={"scope": list(scope)},
        )

    def delete_slot(
        self,
        module_slot_id: str,
        reason: str | None = None,
        scope: Sequence[str] = (),
    ) -> JSONValue:
        _ = reason
        return self.delete_module_slot(module_slot_id, scope)

    def create_capability_binding(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/capability-bindings", json=payload)

    def create_binding(self, payload: JSONDict) -> JSONValue:
        return self.create_capability_binding(payload)

    def get_capability_binding(
        self,
        capability_binding_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/capability-bindings/{capability_binding_id}",
            params={"scope": list(scope)},
        )

    def get_binding(self, capability_binding_id: str, scope: Sequence[str]) -> JSONValue:
        return self.get_capability_binding(capability_binding_id, scope)

    def list_capability_bindings(
        self,
        scope: Sequence[str],
        *,
        module_slot_id: str | None = None,
        status: str | None = None,
        capability_type: str | None = None,
        risk_level: str | None = None,
        extension_package_id: str | None = None,
        include_deleted: bool = False,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {
            "scope": list(scope),
            "include_deleted": include_deleted,
            "limit": limit,
        }
        _set(params, "module_slot_id", module_slot_id)
        _set(params, "status", status)
        _set(params, "capability_type", capability_type)
        _set(params, "risk_level", risk_level)
        _set(params, "extension_package_id", extension_package_id)
        return self._client.get("/brain/capability-bindings", params=params)

    def list_bindings(
        self,
        scope: Sequence[str],
        *,
        module_slot_id: str | None = None,
        status: str | None = None,
        capability_type: str | None = None,
        risk_level: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self.list_capability_bindings(
            scope,
            module_slot_id=module_slot_id,
            status=status,
            capability_type=capability_type,
            risk_level=risk_level,
            limit=limit,
        )

    def disable_capability_binding(
        self,
        capability_binding_id: str,
        payload: JSONDict,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/capability-bindings/{capability_binding_id}/disable",
            json=payload,
            params={"scope": list(scope)},
        )

    def disable_binding(
        self,
        capability_binding_id: str,
        reason: str,
        scope: Sequence[str] = (),
    ) -> JSONValue:
        return self.disable_capability_binding(capability_binding_id, {"reason": reason}, scope)

    def validate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-bindings/validate", json=payload)

    def get_validation(
        self,
        binding_validation_id: str,
        scope: Sequence[str] = (),
    ) -> JSONValue:
        return self._client.get(
            f"/brain/module-bindings/validations/{binding_validation_id}",
            params={"scope": list(scope)},
        )

    def list_conflicts(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "severity", severity)
        _set(params, "module_slot_id", module_slot_id)
        _set(params, "capability_binding_id", capability_binding_id)
        return self._client.get("/brain/module-bindings/conflicts", params=params)

    def conflicts(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self.list_conflicts(scope, status=status, severity=severity, limit=limit)

    def dismiss_conflict(
        self,
        binding_conflict_id: str,
        payload: JSONDict | str,
        scope: Sequence[str] = (),
    ) -> JSONValue:
        request = {"reason": payload} if isinstance(payload, str) else payload
        return self._client.post(
            f"/brain/module-bindings/conflicts/{binding_conflict_id}/dismiss",
            json=request,
            params={"scope": list(scope)},
        )

    def create_mount_plan(
        self,
        payload: JSONDict | str,
        scope: Sequence[str] | None = None,
    ) -> JSONValue:
        if isinstance(payload, str):
            request: JSONDict = {"module_slot_id": payload, "scope": list(scope or ())}
        else:
            request = payload
        return self._client.post("/brain/module-bindings/mount-plans", json=request)

    def create_mount_plan_for_slot(
        self,
        module_slot_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self.create_mount_plan({"module_slot_id": module_slot_id, "scope": list(scope)})

    def get_mount_plan(self, mount_plan_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-bindings/mount-plans/{mount_plan_id}",
            params={"scope": list(scope)},
        )

    def list_mount_plans(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "module_slot_id", module_slot_id)
        return self._client.get("/brain/module-bindings/mount-plans", params=params)

    def create_route_preview(
        self,
        payload: JSONDict | str,
        scope: Sequence[str] | None = None,
    ) -> JSONValue:
        if isinstance(payload, str):
            request: JSONDict = {"capability_binding_id": payload, "scope": list(scope or ())}
        else:
            request = payload
        return self._client.post("/brain/module-bindings/route-previews", json=request)

    def create_route_preview_for_binding(
        self,
        capability_binding_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self.create_route_preview(
            {"capability_binding_id": capability_binding_id, "scope": list(scope)}
        )

    def list_route_previews(
        self,
        scope: Sequence[str],
        *,
        module_slot_id: str | None = None,
        capability_binding_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "module_slot_id", module_slot_id)
        _set(params, "capability_binding_id", capability_binding_id)
        _set(params, "status", status)
        return self._client.get("/brain/module-bindings/route-previews", params=params)

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-bindings/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["ModuleBindingsResource"]
