"""AION-160 actor-context evidence redaction tests."""

import pytest

from aion_brain.contracts.actor_context_resolution import reject_protected_material


@pytest.mark.parametrize(
    "payload",
    [
        {"password": "value"},
        {"Credential": "value"},
        {"authorization-header": "Bearer value"},
        {"nested": [{"Access Token": "value"}]},
        {"nested": ({"refresh_token": "value"},)},
        {"provider_payload": {"claim": "value"}},
        {"message": "contains bearer abc"},
        {"message": "raw identity claim present"},
        {"ｐａｓｓｗｏｒｄ": "value"},
    ],
)
def test_protected_material_is_rejected_from_evidence(payload: object) -> None:
    with pytest.raises(ValueError, match="protected material"):
        reject_protected_material(payload)


def test_safe_counts_and_source_metadata_are_allowed() -> None:
    reject_protected_material(
        {
            "development_value_count": 3,
            "source": "development_simulation",
            "request_context_projected_fields": ("trace_id", "correlation_id"),
        }
    )
