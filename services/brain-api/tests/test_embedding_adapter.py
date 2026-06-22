"""Embedding adapter tests."""

from aion_brain.embeddings.hash_embedding import HashEmbeddingAdapter


def test_hash_embedding_adapter_is_deterministic() -> None:
    """The same text always embeds to the same vector."""
    adapter = HashEmbeddingAdapter(dimensions=16)

    first = adapter.embed_text("alpha beta")
    second = adapter.embed_text("alpha beta")

    assert first == second
    assert first != adapter.embed_text("gamma delta")


def test_hash_embedding_adapter_returns_configured_dimensions() -> None:
    """Hash embeddings honor configured dimensions."""
    adapter = HashEmbeddingAdapter(dimensions=32)

    vector = adapter.embed_text("alpha")

    assert len(vector) == 32
    assert adapter.dimensions() == 32
    assert adapter.model_name() == "hash-embedding-32"


def test_hash_embedding_adapter_empty_text_returns_zero_vector() -> None:
    """Empty text returns a safe zero vector."""
    assert HashEmbeddingAdapter(dimensions=8).embed_text("") == [0.0] * 8
