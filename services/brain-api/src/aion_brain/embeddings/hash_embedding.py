"""Deterministic local hash embedding adapter."""

import hashlib
import math
import re


class HashEmbeddingAdapter:
    """Development-only local embedding adapter with no external calls."""

    def __init__(self, dimensions: int = 384) -> None:
        if dimensions <= 0:
            raise ValueError("embedding dimensions must be positive")
        self._dimensions = dimensions

    def embed_text(self, text: str) -> list[float]:
        """Embed text deterministically using hashed token buckets."""
        vector = [0.0] * self._dimensions
        for token in _tokens(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:8], "big") % self._dimensions
            sign = 1.0 if digest[8] % 2 == 0 else -1.0
            weight = 1.0 + (digest[9] / 255.0)
            vector[index] += sign * weight
        return _normalize(vector)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed multiple text strings deterministically."""
        return [self.embed_text(text) for text in texts]

    def dimensions(self) -> int:
        """Return configured vector dimensions."""
        return self._dimensions

    def model_name(self) -> str:
        """Return the deterministic development model name."""
        return f"hash-embedding-{self._dimensions}"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _normalize(vector: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0.0:
        return vector
    return [value / magnitude for value in vector]
