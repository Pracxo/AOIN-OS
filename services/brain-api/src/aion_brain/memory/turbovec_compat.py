"""Compatibility boundary for optional TurboVec package APIs."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any, cast


class TurboVecCompat:
    """Load and adapt optional TurboVec APIs without leaking vendor objects."""

    def __init__(self) -> None:
        self._module: Any | None = None
        self._reason: str | None = None

    def is_available(self) -> bool:
        """Return whether a turbovec module can be imported."""
        return self._load_module() is not None

    def availability_reason(self) -> str | None:
        """Return why TurboVec is unavailable, if known."""
        self._load_module()
        return self._reason

    def create_index(self, dimensions: int, bit_width: int) -> Any:
        """Create a TurboVec index through known constructor shapes."""
        module = self._require_module()
        index_class = _first_present(module, ("IdMapIndex", "TurboQuantIndex"))
        if index_class is None:
            raise RuntimeError("turbovec_api_incompatible:index_class_missing")
        attempts: tuple[tuple[tuple[Any, ...], dict[str, Any]], ...] = (
            ((), {"dimensions": dimensions, "bit_width": bit_width}),
            ((), {"dim": dimensions, "bits": bit_width}),
            ((dimensions, bit_width), {}),
            ((dimensions,), {"bit_width": bit_width}),
            ((dimensions,), {}),
            ((), {}),
        )
        for args, kwargs in attempts:
            try:
                return index_class(*args, **kwargs)
            except TypeError:
                continue
        raise RuntimeError("turbovec_api_incompatible:index_constructor")

    def load_index(self, path: str) -> Any:
        """Load a TurboVec index from disk through known API shapes."""
        module = self._require_module()
        for method_name in ("load", "read"):
            method = getattr(module, method_name, None)
            if callable(method):
                return method(path)
        index_class = _first_present(module, ("IdMapIndex", "TurboQuantIndex"))
        for method_name in ("load", "read"):
            method = getattr(index_class, method_name, None) if index_class is not None else None
            if callable(method):
                return method(path)
        raise RuntimeError("turbovec_api_incompatible:load_missing")

    def save_index(self, index: Any, path: str) -> None:
        """Persist a TurboVec index through known API shapes."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        for method_name in ("write", "save"):
            method = getattr(index, method_name, None)
            if callable(method):
                method(path)
                return
        module = self._require_module()
        for method_name in ("write", "save"):
            method = getattr(module, method_name, None)
            if callable(method):
                method(index, path)
                return
        raise RuntimeError("turbovec_api_incompatible:save_missing")

    def add_vectors(self, index: Any, vectors: list[list[float]], ids: list[int]) -> None:
        """Add vectors and IDs to an index."""
        if len(vectors) != len(ids):
            raise ValueError("vectors and ids must have the same length")
        method = getattr(index, "add_with_ids", None)
        if callable(method):
            method(vectors, ids)
            return
        method = getattr(index, "add", None)
        if callable(method):
            try:
                method(vectors, ids)
                return
            except TypeError:
                for vector, vector_id in zip(vectors, ids, strict=True):
                    try:
                        method(vector, vector_id)
                    except TypeError:
                        method(vector)
                return
        raise RuntimeError("turbovec_api_incompatible:add_missing")

    def search(
        self,
        index: Any,
        query_vector: list[float],
        limit: int,
        allowed_ids: list[int] | None = None,
    ) -> tuple[list[float], list[int]]:
        """Search an index and return normalized scores with vector IDs."""
        method = getattr(index, "search", None)
        if not callable(method):
            raise RuntimeError("turbovec_api_incompatible:search_missing")
        try:
            raw = method(query_vector, limit, allowed_ids=allowed_ids)
        except TypeError:
            raw = method(query_vector, limit)
        scores, ids = _coerce_search_result(raw)
        if allowed_ids is not None:
            allowed = set(allowed_ids)
            pairs = [(score, vector_id) for score, vector_id in zip(scores, ids, strict=True)]
            pairs = [(score, vector_id) for score, vector_id in pairs if vector_id in allowed]
            scores = [score for score, _ in pairs]
            ids = [vector_id for _, vector_id in pairs]
        return scores[:limit], ids[:limit]

    def remove_ids(self, index: Any, ids: list[int]) -> None:
        """Remove vector IDs from an index when supported."""
        for method_name in ("remove", "delete"):
            method = getattr(index, method_name, None)
            if callable(method):
                try:
                    method(ids)
                except TypeError:
                    for vector_id in ids:
                        method(vector_id)
                return
        raise RuntimeError("turbovec_api_incompatible:remove_missing")

    def _load_module(self) -> Any | None:
        if self._module is not None:
            return self._module
        try:
            self._module = importlib.import_module("turbovec")
            self._reason = None
            return self._module
        except Exception:
            self._reason = "turbovec_package_unavailable"
            return None

    def _require_module(self) -> Any:
        module = self._load_module()
        if module is None:
            raise RuntimeError("turbovec_package_unavailable")
        return module


def _first_present(module: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        value = getattr(module, name, None)
        if value is not None:
            return value
    return None


def _coerce_search_result(raw: Any) -> tuple[list[float], list[int]]:
    if isinstance(raw, tuple) and len(raw) == 2:
        first = list(cast(Any, raw[0]))
        second = list(cast(Any, raw[1]))
        if _looks_like_ids(first) and not _looks_like_ids(second):
            return [_score(value) for value in second], [int(value) for value in first]
        return [_score(value) for value in first], [int(value) for value in second]
    if isinstance(raw, list):
        scores: list[float] = []
        ids: list[int] = []
        for item in raw:
            if isinstance(item, dict):
                vector_id_value = item.get("id")
                if vector_id_value is None:
                    vector_id_value = item.get("vector_id", 0)
                ids.append(int(vector_id_value))
                scores.append(_score(item.get("score", item.get("distance", 0.0))))
            elif isinstance(item, tuple) and len(item) >= 2:
                ids.append(int(item[1]))
                scores.append(_score(item[0]))
        return scores, ids
    raise RuntimeError("turbovec_api_incompatible:search_result")


def _looks_like_ids(values: list[Any]) -> bool:
    return all(
        isinstance(value, int) or (isinstance(value, float) and value.is_integer())
        for value in values
    )


def _score(value: Any) -> float:
    number = float(value)
    return max(0.0, min(1.0, number))
