"""Compatibility matrix and SDK compatibility services."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from importlib.util import find_spec
from pathlib import Path
from typing import Any, cast
from uuid import uuid4

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.config import Settings, get_settings
from aion_brain.contracts.compatibility import CompatibilityMatrix, SDKCompatibilityReport
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.policy.base import PolicyAdapter
from aion_brain.policy.enrichment import enrich_with_internal_dev_actor
from aion_brain.versioning.repository import VersioningRepository

SDK_REQUIRED_RESOURCES = (
    "health",
    "kernel",
    "events",
    "memory",
    "commands",
    "scenarios",
    "versioning",
)


class CompatibilityMatrixService:
    """Generate AION's local compatibility matrix."""

    def __init__(
        self,
        repository: VersioningRepository,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()

    def generate(self, version: str, scope: list[str]) -> CompatibilityMatrix:
        """Generate and persist a local compatibility matrix."""
        self._authorize(
            "compatibility.matrix.generate",
            scope,
            risk_level="medium",
            context={"version": version},
        )
        optional = _optional_adapter_status(self._settings)
        warnings = [
            {"adapter": name, "reason": "optional_adapter_unavailable"}
            for name, status in optional.items()
            if status.get("required") is False and status.get("available") is False
        ]
        status = "warning" if warnings else "compatible"
        matrix = CompatibilityMatrix(
            compatibility_matrix_id=f"compatibility-matrix-{uuid4().hex}",
            version=version,
            api_version=self._settings.api_version,
            sdk_version=_sdk_version(),
            python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            docker_compose_version=None,
            postgres_version="15",
            redis_version="7",
            nats_version="2",
            opa_version="local",
            optional_adapters=optional,
            compatibility={
                "required_components": ["postgres", "redis", "nats", "opa"],
                "warnings": warnings,
                "external_calls": False,
            },
            status=cast(Any, status),
            created_at=datetime.now(UTC),
        )
        saved = self._repository.save_compatibility(matrix)
        self._emit(
            "compatibility_matrix_generated",
            saved.compatibility_matrix_id,
            scope,
            {"version": version, "status": saved.status},
        )
        return saved

    def get(self, version: str, scope: list[str]) -> CompatibilityMatrix | None:
        """Return latest compatibility matrix for a version."""
        self._authorize("compatibility.matrix.read", scope, resource_id=version)
        return self._repository.get_compatibility(version)

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        *,
        resource_id: str | None = None,
        risk_level: str = "low",
        context: dict[str, Any] | None = None,
    ) -> None:
        policy_request = PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            action_type=action_type,
            resource_type="compatibility_matrix",
            resource_id=resource_id,
            risk_level=risk_level,
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context=context or {},
        )
        policy_request = enrich_with_internal_dev_actor(
            policy_request,
            self._settings,
            scope=scope,
            permissions=[action_type],
        )
        decision = self._policy_adapter.authorize(policy_request)
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)

    def _emit(
        self,
        event_type: str,
        node_id: str,
        scope: list[str],
        payload: dict[str, Any],
    ) -> None:
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type=event_type,
            node_type="compatibility",
            node_id=node_id,
            intensity=0.7,
            scope=scope,
            payload=payload,
        )


class SDKCompatibilityService:
    """Check SDK/API surface compatibility without external calls."""

    def __init__(
        self,
        policy_adapter: PolicyAdapter,
        *,
        telemetry_service: object | None = None,
        settings: Settings | None = None,
        sdk_resource_names: list[str] | None = None,
        root_dir: Path | None = None,
    ) -> None:
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._settings = settings or get_settings()
        self._sdk_resource_names = sdk_resource_names
        self._root_dir = root_dir

    def check(self, scope: list[str]) -> SDKCompatibilityReport:
        """Return SDK compatibility status."""
        self._authorize("sdk.compatibility.check", scope)
        checked = list(SDK_REQUIRED_RESOURCES)
        available = set(self._sdk_resource_names or _available_sdk_resources(self._root_dir))
        missing = [resource for resource in checked if resource not in available]
        report = SDKCompatibilityReport(
            report_id=f"sdk-compatibility-{uuid4().hex}",
            api_version=self._settings.api_version,
            sdk_version=_sdk_version(),
            compatible=not missing,
            checked_endpoints=[
                "/health",
                "/brain/kernel/status",
                "/brain/events",
                "/brain/memory/retrieve",
                "/brain/scenarios",
                "/brain/versioning/manifests",
            ],
            missing_endpoints=missing,
            mismatched_contracts=[],
            warnings=[] if not missing else [{"reason": "sdk_resource_missing"}],
            generated_at=datetime.now(UTC),
        )
        emit_versioning_telemetry(
            self._telemetry_service,
            event_type="sdk_compatibility_checked",
            node_type="sdk",
            node_id=report.report_id,
            intensity=0.7 if report.compatible else 1.0,
            scope=scope,
            payload={"compatible": report.compatible},
        )
        return report

    def _authorize(self, action_type: str, scope: list[str]) -> None:
        policy_request = PolicyRequest(
            request_id=f"{action_type}-{uuid4().hex}",
            trace_id=None,
            actor_id=None,
            workspace_id=None,
            action_type=action_type,
            resource_type="sdk_compatibility",
            resource_id=None,
            risk_level="low",
            approval_present=True,
            requested_permissions=[action_type],
            security_scope=scope,
            context={},
        )
        policy_request = enrich_with_internal_dev_actor(
            policy_request,
            self._settings,
            scope=scope,
            permissions=[action_type],
        )
        decision = self._policy_adapter.authorize(policy_request)
        if not decision.allow:
            raise AIONPolicyDeniedException(decision.reason)


def emit_versioning_telemetry(
    telemetry_service: object | None,
    *,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    scope: list[str],
    payload: dict[str, Any],
) -> None:
    """Emit versioning telemetry when a local recorder is configured."""
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-{event_type}-{uuid4().hex}",
                trace_id=node_id,
                event_type=cast(Any, event_type),
                node_type=cast(Any, node_type),
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=intensity,
                payload={"owner_scope": scope, **payload},
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return


def _optional_adapter_status(settings: Settings) -> dict[str, dict[str, object]]:
    adapters = {
        "turbovec": ("turbovec", False),
        "graphiti": ("graphiti", False),
        "mcp": ("mcp", False),
        "temporal": ("temporalio", False),
        "litellm": ("litellm", False),
        "minio": ("minio", False),
        "langfuse": ("langfuse", False),
    }
    return {
        name: {
            "available": find_spec(module_name) is not None,
            "required": required,
            "enabled": _adapter_enabled(name, settings),
        }
        for name, (module_name, required) in adapters.items()
    }


def _adapter_enabled(name: str, settings: Settings) -> bool:
    if name == "mcp":
        return bool(getattr(settings, "mcp_enabled", False))
    if name == "litellm":
        return bool(getattr(settings, "model_gateway_enabled", False))
    if name == "minio":
        return settings.default_object_store == "minio"
    if name == "langfuse":
        return settings.observability_adapter == "langfuse"
    return False


def _available_sdk_resources(root_dir: Path | None = None) -> list[str]:
    resources: list[str] = []
    repo_root = root_dir or Path(__file__).parents[5]
    sdk_resource_dir = repo_root / "packages/aion-sdk-python/src/aion_sdk/resources"
    for name in SDK_REQUIRED_RESOURCES:
        if (sdk_resource_dir / f"{name}.py").is_file() or _sdk_resource_importable(name):
            resources.append(name)
    return resources


def _sdk_resource_importable(name: str) -> bool:
    try:
        return find_spec(f"aion_sdk.resources.{name}") is not None
    except ModuleNotFoundError:
        return False


def _sdk_version() -> str:
    try:
        from importlib.metadata import version

        return version("aion-sdk-python")
    except Exception:
        return "0.1.0"
