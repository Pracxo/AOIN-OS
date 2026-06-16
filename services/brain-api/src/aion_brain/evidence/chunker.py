"""Deterministic evidence chunking."""

from datetime import UTC, datetime

from aion_brain.contracts.evidence import EvidenceChunk
from aion_brain.evidence.content_hash import sha256_text


class EvidenceChunker:
    """Chunk text evidence deterministically."""

    def chunk_text(
        self,
        evidence_id: str,
        text: str,
        chunk_size_chars: int,
        chunk_overlap_chars: int,
    ) -> list[EvidenceChunk]:
        """Create ordered, non-empty chunks for text evidence."""
        if chunk_size_chars <= 0:
            raise ValueError("chunk_size_chars must be positive")
        if chunk_overlap_chars < 0 or chunk_overlap_chars >= chunk_size_chars:
            raise ValueError("chunk_overlap_chars must be smaller than chunk_size_chars")

        chunks: list[EvidenceChunk] = []
        cursor = 0
        index = 0
        step = chunk_size_chars - chunk_overlap_chars
        while cursor < len(text):
            chunk_text = text[cursor : cursor + chunk_size_chars].strip()
            if chunk_text:
                chunks.append(
                    EvidenceChunk(
                        chunk_id=f"{evidence_id}-chunk-{index}",
                        evidence_id=evidence_id,
                        chunk_index=index,
                        text=chunk_text,
                        text_hash=sha256_text(chunk_text),
                        token_count_hint=len(chunk_text.split()),
                        metadata={},
                        created_at=datetime.now(UTC),
                        deleted_at=None,
                    )
                )
                index += 1
            cursor += step
        return chunks
