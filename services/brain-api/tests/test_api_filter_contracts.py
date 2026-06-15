"""API filter contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.api_support.filters import apply_filters_to_items, get_dotted_value
from aion_brain.contracts.api import AIONFilter


def test_filter_rejects_unsafe_field() -> None:
    with pytest.raises(ValidationError):
        AIONFilter(field="name; drop table", operator="equals", value="x")


def test_filter_helper_applies_equals() -> None:
    items = [{"status": "ready"}, {"status": "blocked"}]

    filtered = apply_filters_to_items(
        items,
        [AIONFilter(field="status", operator="equals", value="ready")],
    )

    assert filtered == [{"status": "ready"}]


def test_filter_helper_applies_contains() -> None:
    items = [{"message": "hello brain"}, {"message": "goodbye"}]

    filtered = apply_filters_to_items(
        items,
        [AIONFilter(field="message", operator="contains", value="brain")],
    )

    assert filtered == [{"message": "hello brain"}]


def test_get_dotted_value_reads_nested_dict() -> None:
    assert get_dotted_value({"a": {"b": 3}}, "a.b") == 3
