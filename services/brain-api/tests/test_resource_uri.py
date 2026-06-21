"""Resource URI helper tests."""

from __future__ import annotations

import pytest

from aion_brain.resource_registry.uri import (
    build_resource_uri,
    parse_resource_uri,
    validate_resource_uri,
)


def test_build_and_parse_resource_uri() -> None:
    uri = build_resource_uri("Generic Resource", "id with space", trace_id="trace-1")

    assert uri == "aion://generic_resource/id%20with%20space?trace_id=trace-1"
    parsed = parse_resource_uri(uri)
    assert parsed["resource_type"] == "generic_resource"
    assert parsed["resource_id"] == "id with space"
    assert parsed["trace_id"] == "trace-1"


def test_validate_resource_uri_rejects_invalid_uri() -> None:
    assert validate_resource_uri("aion://generic/id")
    assert not validate_resource_uri("http://example.invalid/id")


def test_build_resource_uri_rejects_empty_id() -> None:
    with pytest.raises(ValueError):
        build_resource_uri("generic", "")
