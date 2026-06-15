"""Application-level backup resource reader boundary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from aion_brain.contracts.backups import BackupResourceType

RESOURCE_TYPES: tuple[BackupResourceType, ...] = (
    "events",
    "memory",
    "semantic_index_metadata",
    "graph",
    "evidence",
    "evidence_links",
    "traces",
    "reasoning",
    "plans",
    "executions",
    "workflows",
    "goals",
    "tasks",
    "schedules",
    "skills",
    "reflections",
    "policy_catalog",
    "identity",
    "autonomy",
    "approvals",
    "modules",
    "sandbox",
    "connectors",
    "scenarios",
    "visual_telemetry",
    "release_metadata",
    "kernel_records",
)

ResourceReader = Callable[[BackupResourceType, list[str]], list[dict[str, Any]]]


@dataclass(frozen=True)
class ResourceReadResult:
    """Records plus non-fatal warnings for a backup resource."""

    resource_type: BackupResourceType
    records: list[dict[str, Any]]
    warnings: list[dict[str, Any]] = field(default_factory=list)


class ResourceReaderRegistry:
    """Registry of application services that can expose backup-safe records."""

    def __init__(
        self,
        readers: dict[BackupResourceType, ResourceReader] | None = None,
    ) -> None:
        self._readers: dict[BackupResourceType, ResourceReader] = dict(readers or {})

    def register(self, resource_type: BackupResourceType, reader: ResourceReader) -> None:
        """Register a backup-safe resource reader."""
        self._readers[resource_type] = reader

    def read(
        self,
        resource_type: BackupResourceType,
        scope: list[str],
        *,
        explicit: bool = False,
    ) -> ResourceReadResult:
        """Read application-level records for one resource."""
        reader = self._readers.get(resource_type)
        if reader is None:
            warning = {
                "resource_type": resource_type,
                "reason": "resource_reader_unavailable",
                "explicit": explicit,
            }
            return ResourceReadResult(resource_type=resource_type, records=[], warnings=[warning])
        records = [_json_record(record) for record in reader(resource_type, scope)]
        return ResourceReadResult(resource_type=resource_type, records=records)

    def existing_ids(self, resource_type: BackupResourceType, scope: list[str]) -> set[str]:
        """Return existing record identifiers for preview conflict checks."""
        return {
            record_id
            for record in self.read(resource_type, scope).records
            if (record_id := record_identifier(record)) is not None
        }


def record_identifier(record: dict[str, Any]) -> str | None:
    """Return the first generic identifier found on a record."""
    for key in (
        "id",
        "event_id",
        "memory_id",
        "trace_id",
        "record_id",
        "capability_id",
        "module_id",
        "goal_id",
        "task_id",
        "workflow_id",
        "approval_request_id",
        "sandbox_profile_id",
        "connector_id",
        "scenario_id",
        "telemetry_id",
        "release_package_id",
        "kernel_record_id",
    ):
        value = record.get(key)
        if value is not None and str(value).strip():
            return str(value)
    return None


def record_in_scope(record: dict[str, Any], scope: list[str]) -> bool:
    """Return true when the record has no scope or overlaps with requested scope."""
    record_scope = record_scope_values(record)
    return not record_scope or bool(set(record_scope) & set(scope))


def record_scope_values(record: dict[str, Any]) -> list[str]:
    """Return scope values from common AION contract fields."""
    for key in ("owner_scope", "security_scope", "scope", "resolved_security_scope"):
        value = record.get(key)
        if isinstance(value, list):
            return [str(item) for item in value]
    workspace_id = record.get("workspace_id")
    if workspace_id is not None:
        return [f"workspace:{workspace_id}"]
    return []


def record_is_deleted(record: dict[str, Any]) -> bool:
    """Return true when a record carries a generic deletion marker."""
    return record.get("deleted_at") is not None or record.get("status") in {
        "deleted",
        "archived",
        "disabled",
    }


def supported_resource(value: str) -> BackupResourceType | None:
    """Return a typed resource when supported."""
    if value in RESOURCE_TYPES:
        return value
    return None


def _json_record(record: dict[str, Any]) -> dict[str, Any]:
    return {str(key): _json_value(value) for key, value in record.items()}


def _json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value
