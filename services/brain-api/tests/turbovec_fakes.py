"""Shared fake TurboVec modules for tests."""

from __future__ import annotations

from types import ModuleType


class FakeIdMapIndex:
    """Tiny fake vector index with the IdMapIndex API shape."""

    saved_paths: list[str] = []

    def __init__(self, dimensions: int = 4, bit_width: int = 4) -> None:
        self.dimensions = dimensions
        self.bit_width = bit_width
        self.vectors: dict[int, list[float]] = {}

    def add_with_ids(self, vectors: list[list[float]], ids: list[int]) -> None:
        for vector, vector_id in zip(vectors, ids, strict=True):
            self.vectors[int(vector_id)] = list(vector)

    def search(
        self,
        query_vector: list[float],
        limit: int,
        allowed_ids: list[int] | None = None,
    ) -> tuple[list[float], list[int]]:
        allowed = set(allowed_ids or self.vectors.keys())
        scored = [
            (_score(query_vector, vector), vector_id)
            for vector_id, vector in self.vectors.items()
            if vector_id in allowed
        ]
        scored.sort(reverse=True)
        return (
            [score for score, _ in scored[:limit]],
            [vector_id for _, vector_id in scored[:limit]],
        )

    def remove(self, ids: list[int]) -> None:
        for vector_id in ids:
            self.vectors.pop(vector_id, None)

    def save(self, path: str) -> None:
        self.saved_paths.append(path)


class FakeTurboQuantIndex(FakeIdMapIndex):
    """Tiny fake vector index with the TurboQuantIndex API shape."""

    def add(self, vectors: list[list[float]], ids: list[int]) -> None:
        self.add_with_ids(vectors, ids)

    def delete(self, ids: list[int]) -> None:
        self.remove(ids)

    def write(self, path: str) -> None:
        self.save(path)


def fake_idmap_module() -> ModuleType:
    """Return a fake turbovec module exposing IdMapIndex."""
    module = ModuleType("turbovec")
    module.IdMapIndex = FakeIdMapIndex  # type: ignore[attr-defined]
    return module


def fake_quant_module() -> ModuleType:
    """Return a fake turbovec module exposing TurboQuantIndex."""
    module = ModuleType("turbovec")
    module.TurboQuantIndex = FakeTurboQuantIndex  # type: ignore[attr-defined]
    return module


def _score(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    return max(0.0, min(1.0, sum(a * b for a, b in zip(left, right, strict=True))))
