"""Embedding adapter interfaces."""

from typing import Protocol


class EmbeddingAdapter(Protocol):
    """Boundary for deterministic or future embedding engines."""

    def embed_text(self, text: str) -> list[float]:
        """Embed one text string."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings."""
        ...

    def dimensions(self) -> int:
        """Return vector dimensions."""
        ...

    def model_name(self) -> str:
        """Return the adapter model name."""
        ...
