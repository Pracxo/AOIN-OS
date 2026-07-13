from __future__ import annotations

import pytest

from aion_brain.production_auth.canonical import canonical_json_text
from aion_brain.production_auth.reason_codes import (
    REASON_CODE_REGISTRY,
    REASON_CODE_REGISTRY_VERSION,
    REQUIRED_REASON_CODES,
    get_reason_code,
    reason_code_registry_payload,
    validate_reason_codes,
)


def test_reason_code_registry_is_immutable_unique_and_ordered() -> None:
    assert len(REQUIRED_REASON_CODES) == len(set(REQUIRED_REASON_CODES))
    assert tuple(REASON_CODE_REGISTRY) == REQUIRED_REASON_CODES

    with pytest.raises(TypeError):
        REASON_CODE_REGISTRY["new_code"] = object()  # type: ignore[index]


def test_reason_code_lookup_and_validation_reject_unknown_or_duplicate_codes() -> None:
    assert get_reason_code("production_auth_runtime_disabled").code == (
        "production_auth_runtime_disabled"
    )

    with pytest.raises(ValueError):
        get_reason_code("unknown")
    with pytest.raises(ValueError):
        validate_reason_codes(("production_auth_runtime_disabled", "unknown"))
    with pytest.raises(ValueError):
        validate_reason_codes(
            ("production_auth_runtime_disabled", "production_auth_runtime_disabled")
        )


def test_reason_code_validation_normalizes_to_registry_order_and_serializes_deterministically() -> (
    None
):
    reversed_codes = tuple(reversed(REQUIRED_REASON_CODES))

    assert validate_reason_codes(reversed_codes) == REQUIRED_REASON_CODES
    payload = reason_code_registry_payload()
    assert payload["reason_code_registry_version"] == REASON_CODE_REGISTRY_VERSION
    assert canonical_json_text(payload) == canonical_json_text(reason_code_registry_payload())
