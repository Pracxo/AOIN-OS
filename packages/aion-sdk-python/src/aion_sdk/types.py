"""Shared SDK JSON type aliases."""

from typing import Any

type JSONDict = dict[str, Any]
type JSONList = list[Any]
type JSONValue = JSONDict | JSONList | str | int | float | bool | None
