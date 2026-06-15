"""Safe in-memory filtering helpers for small AION contract lists."""

from typing import Any

from aion_brain.contracts.api import AIONFilter


def validate_filter(filter: AIONFilter) -> AIONFilter:
    """Return a validated filter contract."""
    return AIONFilter.model_validate(filter.model_dump())


def apply_filters_to_items(
    items: list[dict[str, Any]],
    filters: list[AIONFilter],
) -> list[dict[str, Any]]:
    """Apply safe in-memory filters without SQL generation or eval."""
    result = items
    for filter_item in filters:
        validated = validate_filter(filter_item)
        result = [item for item in result if _matches(item, validated)]
    return result


def get_dotted_value(value: dict[str, Any], field: str) -> Any:
    """Return a nested value by safe dotted path."""
    current: Any = value
    for part in field.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _matches(item: dict[str, Any], filter_item: AIONFilter) -> bool:
    current = get_dotted_value(item, filter_item.field)
    operator = filter_item.operator
    if operator == "equals":
        return bool(current == filter_item.value)
    if operator == "not_equals":
        return bool(current != filter_item.value)
    if operator == "in":
        return current in filter_item.values
    if operator == "not_in":
        return current not in filter_item.values
    if operator == "exists":
        return current is not None
    if operator == "contains":
        return isinstance(current, str) and str(filter_item.value) in current
    if operator == "starts_with":
        return isinstance(current, str) and current.startswith(str(filter_item.value))
    if operator == "ends_with":
        return isinstance(current, str) and current.endswith(str(filter_item.value))
    if operator == "gte":
        if not _comparable(current, filter_item.value):
            return False
        return bool(current >= filter_item.value)
    if operator == "lte":
        if not _comparable(current, filter_item.value):
            return False
        return bool(current <= filter_item.value)
    return False


def _comparable(left: Any, right: Any) -> bool:
    return type(left) is type(right) and isinstance(left, (int, float, str))
