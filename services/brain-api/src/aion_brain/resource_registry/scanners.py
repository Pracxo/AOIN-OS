"""Deterministic local resource scanners."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from aion_brain.contracts.resource_references import ResourceReferenceLink
from aion_brain.contracts.resource_registry import ResourceDescriptor
from aion_brain.resource_registry.descriptors import ResourceDescriptorFactory
from aion_brain.resource_registry.uri import parse_resource_uri, validate_resource_uri


class ResourceScanner:
    """Scan source services through local interfaces and build descriptors."""

    def __init__(
        self,
        descriptor_factory: ResourceDescriptorFactory | None = None,
        **providers: object,
    ) -> None:
        self._descriptor_factory = descriptor_factory or ResourceDescriptorFactory()
        self._providers = providers
        self.warnings: list[dict[str, object]] = []

    def scan(
        self,
        resource_types: list[str],
        source_systems: list[str],
        owner_scope: list[str],
        limit: int,
    ) -> list[ResourceDescriptor]:
        descriptors: list[ResourceDescriptor] = []
        selected = source_systems or sorted(self._providers)
        for source_system in selected:
            provider = self._providers.get(source_system)
            if provider is None:
                self.warnings.append({"source_system": source_system, "reason": "unavailable"})
                continue
            records = _list_provider_records(provider, limit)
            for record in records:
                resource_type = str(record.get("resource_type") or source_system or "generic")
                if resource_types and resource_type not in resource_types:
                    continue
                try:
                    descriptors.append(
                        self._descriptor_factory.from_record(
                            resource_type,
                            record,
                            source_system,
                            owner_scope,
                        )
                    )
                except Exception as exc:
                    self.warnings.append(
                        {
                            "source_system": source_system,
                            "reason": exc.__class__.__name__,
                        }
                    )
        return sorted(descriptors, key=lambda item: item.resource_uri)[:limit]

    def extract_links(self, descriptor: ResourceDescriptor) -> list[ResourceReferenceLink]:
        links: list[ResourceReferenceLink] = []
        for ref in descriptor.refs:
            if not validate_resource_uri(ref):
                continue
            parsed = parse_resource_uri(ref)
            links.append(
                ResourceReferenceLink(
                    resource_link_id=f"resource-link-{uuid4().hex}",
                    trace_id=descriptor.trace_id,
                    source_resource_uri=descriptor.resource_uri,
                    target_resource_uri=ref,
                    source_type=descriptor.resource_type,
                    source_id=descriptor.resource_id,
                    target_type=parsed["resource_type"],
                    target_id=parsed["resource_id"],
                    relation_type="references",
                    status="active",
                    confidence=0.5,
                    discovered_by="resource_scanner",
                    evidence_refs=[],
                    metadata={"source_records_mutated": False},
                )
            )
        return links


def _list_provider_records(provider: object, limit: int) -> list[dict[str, Any]]:
    for name in ("list_registry_records", "list_resources", "list_records", "list"):
        method = getattr(provider, name, None)
        if not callable(method):
            continue
        try:
            value = method(limit=limit)
        except TypeError:
            value = method()
        return [dict(item) for item in list(value or [])[:limit]]
    return []


__all__ = ["ResourceScanner"]
