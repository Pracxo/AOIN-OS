"""Runtime configuration drift helpers."""

from __future__ import annotations

from typing import Any


def compare_config_snapshots(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    """Return deterministic key-level drift between two snapshot payloads."""
    changed: dict[str, Any] = {}
    added: dict[str, Any] = {}
    removed: dict[str, Any] = {}
    for section in ("settings", "feature_flags", "adapter_status"):
        left_section = left.get(section, {})
        right_section = right.get(section, {})
        if not isinstance(left_section, dict) or not isinstance(right_section, dict):
            continue
        left_keys = set(left_section)
        right_keys = set(right_section)
        section_changed = {
            key: {"from": left_section[key], "to": right_section[key]}
            for key in sorted(left_keys & right_keys)
            if left_section[key] != right_section[key]
        }
        if section_changed:
            changed[section] = section_changed
        section_added = {key: right_section[key] for key in sorted(right_keys - left_keys)}
        if section_added:
            added[section] = section_added
        section_removed = {key: left_section[key] for key in sorted(left_keys - right_keys)}
        if section_removed:
            removed[section] = section_removed
    return {
        "changed": changed,
        "added": added,
        "removed": removed,
        "has_drift": bool(changed or added or removed),
    }
