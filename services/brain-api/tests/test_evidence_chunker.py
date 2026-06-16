"""Evidence chunker tests."""

from aion_brain.evidence.chunker import EvidenceChunker


def test_chunker_creates_deterministic_chunks() -> None:
    """Chunk output is deterministic."""
    text = "alpha " * 300
    chunker = EvidenceChunker()

    first = chunker.chunk_text("evidence-1", text, 500, 50)
    second = chunker.chunk_text("evidence-1", text, 500, 50)

    assert [chunk.text_hash for chunk in first] == [chunk.text_hash for chunk in second]
    assert [chunk.chunk_index for chunk in first] == list(range(len(first)))


def test_chunker_creates_no_empty_chunks() -> None:
    """Whitespace-only chunks are not emitted."""
    chunks = EvidenceChunker().chunk_text("evidence-1", "alpha\n\nbeta", 500, 0)

    assert chunks
    assert all(chunk.text.strip() for chunk in chunks)
