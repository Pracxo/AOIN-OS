from __future__ import annotations

import pytest

from aion_brain.model_gateway.context_budget import normalize_model_gateway_context_item


def test_context_item_normalization_does_not_retain_context_body() -> None:
    item = normalize_model_gateway_context_item(
        context_item_id="context-1",
        context_kind="fixture",
        source="local-operator",
        content="redacted local context",
    )
    assert "redacted local context" not in str(item.model_dump())
    assert item.redacted is True
    assert item.item_fingerprint


def test_context_poisoning_with_credentials_is_rejected() -> None:
    with pytest.raises(ValueError):
        normalize_model_gateway_context_item(
            context_item_id="context-2",
            context_kind="fixture",
            source="local-operator",
            content="api_key=secret",
        )
