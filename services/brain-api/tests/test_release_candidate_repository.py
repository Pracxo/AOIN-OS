"""Release candidate repository tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.release_candidate import ReleaseCandidate
from aion_brain.contracts.verification_matrix import VerificationCheck, VerificationMatrix
from aion_brain.release_candidate.repository import ReleaseCandidateRepository


def test_release_candidate_repository_persists_candidate_matrix_and_check() -> None:
    repository = ReleaseCandidateRepository("sqlite+pysqlite:///:memory:")
    candidate = ReleaseCandidate(
        release_candidate_id="rc-1",
        rc_key="rc.test",
        version="0.1.0",
        status="proposed",
        owner_scope=["workspace:main"],
        readiness_score=0.0,
        release_ready=False,
        blocker_count=0,
        warning_count=0,
        metadata={},
    )
    matrix = VerificationMatrix(
        verification_matrix_id="matrix-1",
        matrix_key="rc.test",
        version="0.1.0",
        status="active",
        owner_scope=["workspace:main"],
        required_checks=["tests.brain"],
        optional_checks=[],
        required_threshold=1.0,
        release_ready_threshold=0.95,
        fail_on_critical=True,
        fail_on_missing_required=True,
        metadata={},
    )
    check = VerificationCheck(
        verification_check_id="check-1",
        check_key="tests.brain",
        check_type="unit_tests",
        status="passed",
        severity="low",
        required=True,
        passed=True,
        title="Brain tests",
        summary="passed",
        evidence={"source": "test"},
        created_at=datetime.now(UTC),
    )

    repository.save_candidate(candidate)
    repository.save_matrix(matrix)
    repository.save_check(check)

    assert repository.get_candidate("rc-1") is not None
    assert repository.get_matrix("matrix-1") is not None
    assert repository.list_checks(rc_run_id=None)[0].check_key == "tests.brain"
