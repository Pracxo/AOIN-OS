"""Canonical AION resource URI helpers."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, quote, unquote, urlparse

from aion_brain.contracts.model_outputs import reject_hidden_or_secret_text

_SNAKE_RE = re.compile(r"[^a-z0-9]+")


def normalize_resource_type(resource_type: str) -> str:
    """Normalize a resource type to lowercase snake_case."""
    lowered = resource_type.strip().lower()
    normalized = _SNAKE_RE.sub("_", lowered).strip("_")
    if not normalized:
        raise ValueError("resource_type cannot be empty")
    return normalized


def build_resource_uri(resource_type: str, resource_id: str, trace_id: str | None = None) -> str:
    """Build a canonical `aion://{resource_type}/{resource_id}` URI."""
    normalized_type = normalize_resource_type(resource_type)
    if not resource_id:
        raise ValueError("resource_id cannot be empty")
    reject_hidden_or_secret_text(resource_id, "resource_id")
    encoded_id = quote(resource_id, safe="")
    uri = f"aion://{normalized_type}/{encoded_id}"
    if trace_id:
        reject_hidden_or_secret_text(trace_id, "trace_id")
        uri = f"{uri}?trace_id={quote(trace_id, safe='')}"
    return uri


def parse_resource_uri(resource_uri: str) -> dict[str, str]:
    """Parse a canonical AION URI."""
    reject_hidden_or_secret_text(resource_uri, "resource_uri")
    parsed = urlparse(resource_uri)
    if parsed.scheme != "aion" or not parsed.netloc or not parsed.path.strip("/"):
        raise ValueError("invalid AION resource URI")
    resource_type = normalize_resource_type(parsed.netloc)
    resource_id = unquote(parsed.path.strip("/"))
    if not resource_id:
        raise ValueError("resource_id cannot be empty")
    result = {"resource_type": resource_type, "resource_id": resource_id}
    query = parse_qs(parsed.query)
    if "trace_id" in query and query["trace_id"]:
        result["trace_id"] = query["trace_id"][0]
    return result


def validate_resource_uri(resource_uri: str) -> bool:
    """Return true when a string is a valid safe AION resource URI."""
    try:
        parse_resource_uri(resource_uri)
    except Exception:
        return False
    return True


__all__ = [
    "build_resource_uri",
    "normalize_resource_type",
    "parse_resource_uri",
    "validate_resource_uri",
]
