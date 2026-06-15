"""Evidence contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.evidence import (
    EvidenceChunk,
    EvidenceIngestRequest,
    EvidenceRecord,
    GroundingRequest,
    GroundingStatement,
)


def test_evidence_record_validates_source_type() -> None:
    """Evidence source types are restricted to generic values."""
    with pytest.raises(ValidationError):
        make_evidence(source_type="finance")  # type: ignore[arg-type]


def test_evidence_record_rejects_empty_owner_scope() -> None:
    """Evidence owner scope is required."""
    with pytest.raises(ValidationError):
        make_evidence(owner_scope=[])


def test_evidence_record_rejects_secret_metadata() -> None:
    """Evidence metadata rejects secret-like keys."""
    with pytest.raises(ValidationError):
        make_evidence(metadata={"api_key": "hidden"})


def test_evidence_ingest_requires_content_text_or_ref() -> None:
    """Evidence ingestion needs text or a metadata-only reference."""
    with pytest.raises(ValidationError):
        EvidenceIngestRequest(
            source_type="text",
            source_ref=None,
            owner_scope=["workspace:main"],
            title="Evidence",
            content_text=None,
            content_ref=None,
        )


def test_evidence_ingest_validates_chunk_sizes() -> None:
    """Chunk size and overlap bounds are validated."""
    with pytest.raises(ValidationError):
        EvidenceIngestRequest(
            source_type="text",
            source_ref=None,
            owner_scope=["workspace:main"],
            title="Evidence",
            content_text="alpha",
            chunk_size_chars=500,
            chunk_overlap_chars=500,
        )


def test_evidence_chunk_validates_chunk_index() -> None:
    """Chunk indexes cannot be negative."""
    with pytest.raises(ValidationError):
        EvidenceChunk(
            chunk_id="chunk-1",
            evidence_id="evidence-1",
            chunk_index=-1,
            text="alpha",
            text_hash="hash",
            token_count_hint=1,
            metadata={},
            created_at=datetime.now(UTC),
            deleted_at=None,
        )


def test_grounding_request_rejects_empty_statements() -> None:
    """Grounding requires at least one statement."""
    with pytest.raises(ValidationError):
        GroundingRequest(trace_id=None, statements=[], scope=["workspace:main"])


def make_evidence(**updates: object) -> EvidenceRecord:
    """Create an evidence record."""
    values = {
        "evidence_id": "evidence-1",
        "trace_id": None,
        "source_type": "text",
        "source_ref": None,
        "owner_scope": ["workspace:main"],
        "title": "Evidence",
        "summary": "alpha beta",
        "content_hash": "hash",
        "content_ref": "evidence://evidence-1",
        "media_type": "text/plain",
        "sensitivity": "internal",
        "confidence": 0.9,
        "metadata": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
        "deleted_at": None,
    }
    values.update(updates)
    return EvidenceRecord.model_validate(values)


def make_statement(statement: str = "alpha beta") -> GroundingStatement:
    """Create a grounding statement."""
    return GroundingStatement(statement_id="statement-1", statement=statement)

