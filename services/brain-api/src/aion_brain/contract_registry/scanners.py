"""Deterministic local contract and interface scanners."""

from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
import re
from pathlib import Path
from typing import Any, cast, get_args
from uuid import uuid4

from fastapi.routing import APIRoute
from pydantic import BaseModel

from aion_brain.config import Settings, get_settings
from aion_brain.contract_registry.hash import hash_schema
from aion_brain.contract_registry.redaction import (
    contains_disallowed_domain_term,
    redact_contract_payload,
)
from aion_brain.contracts.contract_registry import ContractIndexRecord, InterfaceInventoryRecord

_REPO_ROOT = Path(__file__).resolve().parents[5]
_BRAIN_SRC = Path(__file__).resolve().parents[1]
_SDK_ROOT = _REPO_ROOT / "packages/aion-sdk-python/src/aion_sdk"
_REGO_PATH = _REPO_ROOT / "infra/opa/policies/brain.rego"


class ContractScanner:
    """Scan AION-owned interface shapes without mutating source files."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        sdk_root: Path | None = None,
        policy_file: Path | None = None,
        app_routes: list[APIRoute] | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.sdk_root = sdk_root or _SDK_ROOT
        self.policy_file = policy_file or _REGO_PATH
        self.app_routes = app_routes
        self.warnings: list[dict[str, object]] = []

    def scan_pydantic_contracts(self, owner_scope: list[str]) -> list[ContractIndexRecord]:
        records: list[ContractIndexRecord] = []
        for _, module_name, _ in pkgutil.iter_modules([str(_BRAIN_SRC / "contracts")]):
            full_name = f"aion_brain.contracts.{module_name}"
            try:
                module = importlib.import_module(full_name)
            except Exception as exc:
                self._warn("pydantic_contracts", full_name, exc)
                continue
            for symbol, value in inspect.getmembers(module, inspect.isclass):
                if not issubclass(value, BaseModel) or value is BaseModel:
                    continue
                if value.__module__ != full_name:
                    continue
                try:
                    schema = cast(
                        dict[str, Any], redact_contract_payload(value.model_json_schema())
                    )
                    contract_key = f"{full_name}.{symbol}"
                    if contains_disallowed_domain_term({"contract_key": contract_key}):
                        continue
                    records.append(
                        ContractIndexRecord(
                            contract_index_id=f"contract-index-{uuid4().hex}",
                            contract_key=contract_key,
                            contract_type="pydantic_model",
                            source_path=_source_path(value),
                            source_symbol=symbol,
                            status="active",
                            visibility="public",
                            version=self.settings.version,
                            schema_hash=hash_schema(schema),
                            schema=schema,
                            owner_scope=owner_scope,
                            tags=["pydantic", "contract"],
                            metadata={"source_of_truth": "source_code", "source_mutated": False},
                        )
                    )
                except Exception as exc:
                    self._warn("pydantic_contracts", f"{full_name}.{symbol}", exc)
        return sorted(records, key=lambda item: item.contract_key)

    def scan_api_routes(self, owner_scope: list[str]) -> list[InterfaceInventoryRecord]:
        records: list[InterfaceInventoryRecord] = []
        for route in self._routes():
            methods = sorted(route.methods or [])
            for method in methods:
                if method in {"HEAD", "OPTIONS"}:
                    continue
                descriptor = {
                    "path": route.path,
                    "method": method,
                    "name": route.name,
                    "tags": list(route.tags or []),
                    "response_model": _type_name(route.response_model),
                }
                descriptor = cast(dict[str, Any], redact_contract_payload(descriptor))
                interface_key = f"{method} {route.path}"
                records.append(
                    InterfaceInventoryRecord(
                        interface_id=f"interface-api-{uuid4().hex}",
                        interface_key=interface_key,
                        interface_type="health_check"
                        if route.path.startswith("/health")
                        else "api_route",
                        source_system="fastapi",
                        status="active",
                        visibility="public",
                        version=self.settings.version,
                        path=route.path,
                        method=method,
                        schema_hash=hash_schema(descriptor),
                        descriptor=descriptor,
                        owner_scope=owner_scope,
                        metadata={"source_mutated": False},
                    )
                )
        return sorted(records, key=lambda item: item.interface_key)

    def scan_sdk_resources(self, owner_scope: list[str]) -> list[InterfaceInventoryRecord]:
        resources_dir = self.sdk_root / "resources"
        records: list[InterfaceInventoryRecord] = []
        for path in sorted(resources_dir.glob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                tree = ast.parse(path.read_text())
            except OSError as exc:
                self._warn("sdk_resources", str(path), exc)
                continue
            for node in tree.body:
                if not isinstance(node, ast.ClassDef) or not node.name.endswith("Resource"):
                    continue
                methods = [
                    item.name
                    for item in node.body
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith("_")
                ]
                descriptor = {
                    "resource": node.name,
                    "methods": sorted(methods),
                    "source_path": _safe_relative(path),
                }
                records.append(
                    InterfaceInventoryRecord(
                        interface_id=f"interface-sdk-resource-{uuid4().hex}",
                        interface_key=f"sdk.resource.{path.stem}",
                        interface_type="sdk_resource",
                        source_system="aion_sdk",
                        status="active",
                        visibility="sdk",
                        version=self.settings.version,
                        resource_type=path.stem,
                        schema_hash=hash_schema(descriptor),
                        descriptor=descriptor,
                        owner_scope=owner_scope,
                        metadata={"source_mutated": False},
                    )
                )
                for method in methods:
                    method_descriptor = {
                        "resource": node.name,
                        "method": method,
                        "source_path": _safe_relative(path),
                    }
                    records.append(
                        InterfaceInventoryRecord(
                            interface_id=f"interface-sdk-method-{uuid4().hex}",
                            interface_key=f"sdk.{path.stem}.{method}",
                            interface_type="sdk_method",
                            source_system="aion_sdk",
                            status="active",
                            visibility="sdk",
                            version=self.settings.version,
                            command=method,
                            resource_type=path.stem,
                            schema_hash=hash_schema(method_descriptor),
                            descriptor=method_descriptor,
                            owner_scope=owner_scope,
                            metadata={"source_mutated": False},
                        )
                    )
        return sorted(records, key=lambda item: item.interface_key)

    def scan_cli_commands(self, owner_scope: list[str]) -> list[InterfaceInventoryRecord]:
        commands_dir = self.sdk_root / "cli/commands"
        records: list[InterfaceInventoryRecord] = []
        for path in sorted(commands_dir.glob("*.py")):
            if path.name == "__init__.py":
                continue
            try:
                tree = ast.parse(path.read_text())
            except OSError as exc:
                self._warn("cli_commands", str(path), exc)
                continue
            group = path.stem.replace("_", "-")
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef):
                    continue
                command_name = _typer_command_name(node)
                if command_name is None:
                    continue
                command = f"{group} {command_name}".strip()
                descriptor = {
                    "command": command,
                    "function": node.name,
                    "source_path": _safe_relative(path),
                }
                records.append(
                    InterfaceInventoryRecord(
                        interface_id=f"interface-cli-{uuid4().hex}",
                        interface_key=f"cli.{command.replace(' ', '.')}",
                        interface_type="cli_command",
                        source_system="aionctl",
                        status="active",
                        visibility="cli",
                        version=self.settings.version,
                        command=command,
                        schema_hash=hash_schema(descriptor),
                        descriptor=descriptor,
                        owner_scope=owner_scope,
                        metadata={"source_mutated": False},
                    )
                )
        return sorted(records, key=lambda item: item.interface_key)

    def scan_policy_actions(self, owner_scope: list[str]) -> list[InterfaceInventoryRecord]:
        try:
            text = self.policy_file.read_text()
        except OSError as exc:
            self._warn("policy_actions", str(self.policy_file), exc)
            return []
        actions = sorted(
            {
                match
                for match in re.findall(r'"([a-zA-Z0-9_.:-]+)"', text)
                if "." in match and not match.startswith("workspace:")
            }
        )
        return [
            self._interface(
                owner_scope,
                interface_key=f"policy.{action}",
                interface_type="policy_action",
                source_system="opa",
                visibility="internal",
                descriptor={
                    "action": action,
                    "policy_file": _safe_relative(self.policy_file),
                },
                action=action,
            )
            for action in actions
        ]

    def scan_env_settings(self, owner_scope: list[str]) -> list[InterfaceInventoryRecord]:
        records: list[InterfaceInventoryRecord] = []
        for key, field in sorted(Settings.model_fields.items()):
            descriptor = {
                "setting_key": key,
                "annotation": str(field.annotation),
                "default": redact_contract_payload(field.default),
                "validation_alias": str(field.validation_alias),
            }
            records.append(
                self._interface(
                    owner_scope,
                    interface_key=f"env.{key}",
                    interface_type="env_setting",
                    source_system="settings",
                    visibility="internal",
                    descriptor=descriptor,
                    setting_key=key,
                )
            )
        return records

    def scan_telemetry_vocab(self, owner_scope: list[str]) -> list[InterfaceInventoryRecord]:
        from aion_brain.contracts.telemetry import VisualNodeType, VisualTelemetryEventType

        records = [
            self._interface(
                owner_scope,
                interface_key=f"telemetry.event.{event_type}",
                interface_type="telemetry_event",
                source_system="visual_telemetry",
                visibility="internal",
                descriptor={"event_type": event_type},
                telemetry_key=str(event_type),
            )
            for event_type in sorted(get_args(VisualTelemetryEventType))
        ]
        records.extend(
            self._interface(
                owner_scope,
                interface_key=f"telemetry.node.{node_type}",
                interface_type="telemetry_node",
                source_system="visual_telemetry",
                visibility="internal",
                descriptor={"node_type": node_type},
                telemetry_key=str(node_type),
            )
            for node_type in sorted(get_args(VisualNodeType))
        )
        return records

    def scan_registry_resource_types(
        self, owner_scope: list[str]
    ) -> list[InterfaceInventoryRecord]:
        resource_types = (
            "contract_snapshot",
            "compatibility_scan",
            "interface_drift",
            "migration_note",
            "contract_report",
        )
        return [
            self._interface(
                owner_scope,
                interface_key=f"registry_resource.{resource_type}",
                interface_type="registry_resource",
                source_system="contract_registry",
                visibility="internal",
                descriptor={"resource_type": resource_type},
                resource_type=resource_type,
            )
            for resource_type in resource_types
        ]

    def scan_all(
        self,
        owner_scope: list[str],
        scan_scope: list[str] | None = None,
    ) -> dict[str, Any]:
        selected = set(scan_scope or [])
        include_all = not selected

        def include(name: str) -> bool:
            return include_all or name in selected

        contracts: list[ContractIndexRecord] = []
        interfaces: list[InterfaceInventoryRecord] = []
        if include("pydantic_contracts"):
            contracts.extend(self.scan_pydantic_contracts(owner_scope))
        if include("api_routes"):
            interfaces.extend(self.scan_api_routes(owner_scope))
        if include("sdk_resources"):
            interfaces.extend(self.scan_sdk_resources(owner_scope))
        if include("cli_commands"):
            interfaces.extend(self.scan_cli_commands(owner_scope))
        if include("policy_actions"):
            interfaces.extend(self.scan_policy_actions(owner_scope))
        if include("env_settings"):
            interfaces.extend(self.scan_env_settings(owner_scope))
        if include("telemetry_vocab"):
            interfaces.extend(self.scan_telemetry_vocab(owner_scope))
        if include("registry_resource_types"):
            interfaces.extend(self.scan_registry_resource_types(owner_scope))
        return {
            "contracts": contracts,
            "interfaces": interfaces,
            "warnings": list(self.warnings),
            "source_mutated": False,
        }

    def _interface(
        self,
        owner_scope: list[str],
        *,
        interface_key: str,
        interface_type: str,
        source_system: str,
        visibility: str,
        descriptor: dict[str, Any],
        path: str | None = None,
        method: str | None = None,
        command: str | None = None,
        action: str | None = None,
        setting_key: str | None = None,
        feature_key: str | None = None,
        telemetry_key: str | None = None,
        resource_type: str | None = None,
    ) -> InterfaceInventoryRecord:
        descriptor = cast(dict[str, Any], redact_contract_payload(descriptor))
        return InterfaceInventoryRecord(
            interface_id=f"interface-{uuid4().hex}",
            interface_key=interface_key,
            interface_type=cast(Any, interface_type),
            source_system=source_system,
            status="active",
            visibility=cast(Any, visibility),
            version=self.settings.version,
            path=path,
            method=method,
            command=command,
            action=action,
            setting_key=setting_key,
            feature_key=feature_key,
            telemetry_key=telemetry_key,
            resource_type=resource_type,
            schema_hash=hash_schema(descriptor),
            descriptor=descriptor,
            owner_scope=owner_scope,
            metadata={"source_mutated": False},
        )

    def _routes(self) -> list[APIRoute]:
        if self.app_routes is not None:
            return self.app_routes
        try:
            app_factory = importlib.import_module("aion_brain.kernel.app_factory")
            routers = getattr(app_factory, "ROUTERS", ())
        except Exception as exc:
            self._warn("api_routes", "aion_brain.kernel.app_factory", exc)
            return []
        routes: list[APIRoute] = []
        for router in routers:
            routes.extend(
                route for route in getattr(router, "routes", []) if isinstance(route, APIRoute)
            )
        return routes

    def _warn(self, scanner: str, target: str, exc: Exception) -> None:
        self.warnings.append(
            {"scanner": scanner, "target": target, "reason": exc.__class__.__name__}
        )


def _source_path(model: type[BaseModel]) -> str:
    try:
        path = Path(inspect.getfile(model))
        return _safe_relative(path)
    except Exception:
        return model.__module__


def _safe_relative(path: Path) -> str:
    try:
        return str(path.relative_to(_REPO_ROOT))
    except ValueError:
        return str(path)


def _type_name(value: object) -> str | None:
    if value is None:
        return None
    return getattr(value, "__name__", str(value))


def _typer_command_name(node: ast.FunctionDef) -> str | None:
    for decorator in node.decorator_list:
        call = decorator if isinstance(decorator, ast.Call) else None
        if call is None:
            continue
        func = call.func
        if not isinstance(func, ast.Attribute) or func.attr != "command":
            continue
        if (
            call.args
            and isinstance(call.args[0], ast.Constant)
            and isinstance(call.args[0].value, str)
        ):
            return call.args[0].value
        return node.name.replace("_", "-")
    return None


__all__ = ["ContractScanner"]
