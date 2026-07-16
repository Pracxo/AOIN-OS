from __future__ import annotations

import copy
import math
from datetime import UTC, datetime, timedelta, timezone

import pytest

from aion_brain.production_auth.canonical import (
    canonical_json_bytes,
    canonical_json_text,
    sha256_fingerprint,
)


def test_canonical_json_is_deterministic_sorted_compact_utf8_and_non_mutating() -> None:
    payload = {"z": "AION", "a": {"b": [2, 1]}, "unicode": "stabilization"}
    original = copy.deepcopy(payload)

    first = canonical_json_text(payload)
    second = canonical_json_text({"unicode": "stabilization", "a": {"b": [2, 1]}, "z": "AION"})

    assert first == second
    assert first.startswith('{"a":')
    assert ", " not in first
    assert payload == original
    assert canonical_json_bytes(payload) == first.encode("utf-8")


def test_canonical_json_normalizes_datetimes_to_utc() -> None:
    payload = {
        "naive": datetime(2026, 7, 13, 12, 30, 0),
        "aware": datetime(2026, 7, 13, 7, 30, 0, tzinfo=timezone(timedelta(hours=-5))),
    }

    text = canonical_json_text(payload)

    assert '"naive":"2026-07-13T12:30:00Z"' in text
    assert '"aware":"2026-07-13T12:30:00Z"' in text
    assert sha256_fingerprint(payload) == sha256_fingerprint(payload)


def test_canonical_json_rejects_unsupported_or_non_finite_values() -> None:
    with pytest.raises(TypeError):
        canonical_json_text({"bad": object()})

    with pytest.raises(TypeError):
        canonical_json_text({"bad": math.nan})

    with pytest.raises(TypeError):
        canonical_json_text({1: "non-string key"})

    with pytest.raises(TypeError):
        canonical_json_text({"unordered": {"set-values"}})


def test_canonical_json_does_not_use_memory_address_representations() -> None:
    payload = {"created_at": datetime(2026, 7, 13, tzinfo=UTC), "items": ("a", "b")}

    text = canonical_json_text(payload)

    assert "object at 0x" not in text
    assert '"items":["a","b"]' in text
