"""Resource descriptor factory."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast, get_args

from aion_brain.contracts.resource_registry import (
    ResourceDescriptor,
    ResourceSensitivity,
    ResourceStatus,
    ResourceType,
    ResourceVisibility,
)
from aion_brain.resource_registry.redaction import (
    redact_registry_payload,
    redact_registry_refs,
    redact_registry_text,
)
from aion_brain.resource_registry.uri import build_resource_uri, normalize_resource_type

_ALLOWED_RESOURCE_TYPES = set(get_args(ResourceType))


class ResourceDescriptorFactory:
    """Build safe registry descriptors from source-system record metadata."""

    def minimal(
        self,
        resource_type: str,
        resource_id: str,
        source_system: str,
        owner_scope: list[str],
    ) -> ResourceDescriptor:
        normalized = _supported_resource_type(resource_type)
        uri = build_resource_uri(normalized, resource_id)
        now = datetime.now(UTC)
        return ResourceDescriptor(
            resource_uri=uri,
            resource_type=cast(ResourceType, normalized),
            resource_id=resource_id,
            source_system=source_system,
            status="active",
            visibility="internal",
            sensitivity="internal",
            title=f"{normalized}:{resource_id}",
            summary="Minimal registry descriptor.",
            owner_scope=owner_scope,
            tags=[],
            refs=[],
            metadata={"registry_descriptor_only": True},
            content_hash=None,
            first_seen_at=now,
            last_seen_at=now,
        )

    def from_record(
        self,
        resource_type: str,
        record: dict[str, Any],
        source_system: str,
        owner_scope: list[str],
    ) -> ResourceDescriptor:
        normalized = _supported_resource_type(resource_type)
        resource_id = str(
            record.get("resource_id")
            or record.get(f"{normalized}_id")
            or record.get("id")
            or record.get("record_id")
            or ""
        )
        if not resource_id:
            raise ValueError("record must include an identifier")
        trace_id = _optional_str(record.get("trace_id"))
        now = datetime.now(UTC)
        return ResourceDescriptor(
            resource_uri=build_resource_uri(normalized, resource_id, trace_id=trace_id),
            resource_type=cast(ResourceType, normalized),
            resource_id=resource_id,
            trace_id=trace_id,
            actor_id=_optional_str(record.get("actor_id")),
            workspace_id=_optional_str(record.get("workspace_id")),
            source_system=source_system,
            status=cast(ResourceStatus, str(record.get("status") or "active")),
            visibility=cast(ResourceVisibility, str(record.get("visibility") or "internal")),
            sensitivity=cast(ResourceSensitivity, str(record.get("sensitivity") or "internal")),
            title=redact_registry_text(
                str(record.get("title") or record.get("name") or f"{normalized}:{resource_id}")
            ),
            summary=redact_registry_text(
                str(record.get("summary") or record.get("description") or "Indexed AION record.")
            ),
            owner_scope=list(record.get("owner_scope") or owner_scope),
            tags=[str(tag) for tag in record.get("tags", [])],
            refs=redact_registry_refs(_extract_refs(record)),
            metadata=cast(dict[str, Any], redact_registry_payload(record.get("metadata", {}))),
            content_hash=_optional_str(record.get("content_hash") or record.get("hash")),
            first_seen_at=_optional_datetime(record.get("first_seen_at")) or now,
            last_seen_at=_optional_datetime(record.get("last_seen_at")) or now,
            deleted_at=_optional_datetime(record.get("deleted_at")),
            archived_at=_optional_datetime(record.get("archived_at")),
        )


def _optional_str(value: object) -> str | None:
    return str(value) if value not in (None, "") else None


def _optional_datetime(value: object) -> datetime | None:
    return value if isinstance(value, datetime) else None


def _supported_resource_type(resource_type: str) -> str:
    normalized = normalize_resource_type(resource_type)
    return normalized if normalized in _ALLOWED_RESOURCE_TYPES else "generic"


def _extract_refs(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key, value in record.items():
        if key == "refs" and isinstance(value, list):
            refs.extend(str(item) for item in value)
        elif key.endswith("_refs") and isinstance(value, list):
            refs.extend(str(item) for item in value)
    return refs


__all__ = ["ResourceDescriptorFactory"]
