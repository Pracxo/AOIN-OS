"""Backlink service tests."""

from __future__ import annotations

from aion_brain.contracts.resource_references import ResourceReferenceCreateRequest
from aion_brain.resource_registry.links import BacklinkService, ResourceLinkService
from tests.kernel_fakes import AllowPolicy
from tests.resource_registry_helpers import repository


def test_backlink_service_lists_target_backlinks() -> None:
    repo = repository()
    ResourceLinkService(repo, AllowPolicy()).create_link(
        ResourceReferenceCreateRequest(
            source_resource_uri="aion://generic/source",
            target_resource_uri="aion://generic/target",
        ),
        ["workspace:main"],
    )

    backlinks = BacklinkService(repo, AllowPolicy()).list_backlinks(
        "aion://generic/target",
        ["workspace:main"],
    )

    assert backlinks[0]["referring_resource_uri"] == "aion://generic/source"


def test_backlink_service_rebuilds_without_source_mutation() -> None:
    repo = repository()
    ResourceLinkService(repo, AllowPolicy()).create_link(
        ResourceReferenceCreateRequest(
            source_resource_uri="aion://generic/source",
            target_resource_uri="aion://generic/target",
        ),
        ["workspace:main"],
    )

    result = BacklinkService(repo, AllowPolicy()).rebuild_backlinks(["workspace:main"])

    assert result["links_seen"] == 1
    assert result["backlinks_written"] == 0
