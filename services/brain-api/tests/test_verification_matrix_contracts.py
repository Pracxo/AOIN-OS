"""Verification matrix contract tests."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.verification_matrix import VerificationCheck, VerificationMatrix


def test_verification_check_status_and_passed_must_match() -> None:
    with pytest.raises(ValidationError):
        VerificationCheck(
            verification_check_id="check-1",
            check_key="tests.brain",
            check_type="unit_tests",
            status="failed",
            severity="critical",
            required=True,
            passed=True,
            title="Brain tests",
            summary="failed",
            created_at=datetime.now(UTC),
        )


def test_verification_matrix_rejects_invalid_check_key() -> None:
    with pytest.raises(ValidationError):
        VerificationMatrix(
            verification_matrix_id="matrix-1",
            matrix_key="rc.test",
            version="0.1.0",
            status="active",
            owner_scope=["workspace:main"],
            required_checks=["Bad Check"],
            optional_checks=[],
            required_threshold=1.0,
            release_ready_threshold=0.95,
            fail_on_critical=True,
            fail_on_missing_required=True,
            metadata={},
        )
