"""Release candidate contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.release_candidate import (
    RCEvidencePack,
    ReleaseCandidate,
    ReleaseCandidateCreateRequest,
)


def test_release_candidate_requires_dotted_lowercase_key() -> None:
    with pytest.raises(ValidationError):
        ReleaseCandidateCreateRequest(
            rc_key="Bad Key",
            version="0.1.0",
            owner_scope=["workspace:main"],
        )


def test_release_candidate_blocks_release_ready_when_blockers_exist() -> None:
    candidate = ReleaseCandidate(
        release_candidate_id="rc-1",
        rc_key="rc.test",
        version="0.1.0",
        status="blocked",
        owner_scope=["workspace:main"],
        readiness_score=1.0,
        release_ready=True,
        blocker_count=1,
        warning_count=0,
        metadata={},
    )

    assert candidate.release_ready is False


def test_rc_evidence_pack_rejects_secret_like_report_payload() -> None:
    with pytest.raises(ValidationError):
        RCEvidencePack(
            evidence_pack_id="pack-1",
            status="created",
            owner_scope=["workspace:main"],
            pack_type="rc",
            title="pack",
            summary="summary",
            report_hash="hash",
            redacted_report={"api_key": "secret"},
            created_at=datetime.now(UTC),
        )
