from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from knowledge_research_test_helpers import NOW, sha256_bytes
from pydantic import ValidationError

from aion_brain.knowledge_intelligence.source_snapshot import (
    EphemeralSourceArtifact,
    SourceSnapshot,
)


def valid_snapshot() -> SourceSnapshot:
    body = b"synthetic body"
    return SourceSnapshot(
        snapshot_id="source-snapshot-0001",
        plan_id="plan-001",
        candidate_id="candidate-001",
        query_ids=("query-001",),
        original_url_fingerprint="a" * 64,
        canonical_url="https://research.example.invalid/source.txt",
        final_url="https://research.example.invalid/source.txt",
        method="GET",
        status_code=200,
        content_type="text/plain",
        character_encoding="utf-8",
        content_length=len(body),
        content_sha256=sha256_bytes(body),
        safe_headers={"Content-Type": "text/plain"},
        redirect_chain=(),
        source_class="official_standard",
        robots_policy_status="allowed",
        licence_policy_status="permitted",
        retrieval_timestamp=NOW,
        content_artifact_id="artifact-source-snapshot-0001",
        content_present_in_memory=True,
        redacted_preview="synthetic body",
        snapshot_fingerprint="b" * 64,
    )


def test_source_snapshot_is_immutable_metadata_and_body_excluded_from_repr():
    snapshot = valid_snapshot()
    with pytest.raises(ValidationError):
        SourceSnapshot.model_validate({**snapshot.model_dump(), "verified_fact": True})
    assert "synthetic body" in snapshot.redacted_preview
    artifact = EphemeralSourceArtifact(
        snapshot_id=snapshot.snapshot_id,
        content_bytes=b"synthetic body",
        content_sha256=sha256_bytes(b"synthetic body"),
    )
    assert "synthetic body" not in repr(artifact)
    with pytest.raises(FrozenInstanceError):
        artifact.content_bytes = b"changed"  # type: ignore[misc]
