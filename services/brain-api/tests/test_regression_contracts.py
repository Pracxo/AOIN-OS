"""Regression contract validation tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.regression import RegressionCase, RegressionRunRequest


def test_regression_case_rejects_empty_scope() -> None:
    """Golden cases always carry an ownership scope."""
    with pytest.raises(ValidationError):
        RegressionCase(
            case_id="case-1",
            name="Stable planning",
            description="A generic stable trace.",
            source_trace_id="trace-1",
            input_snapshot_id="snapshot-1",
            expected_snapshot_id="snapshot-2",
            owner_scope=[],
            status="active",
            tags=[],
            metadata={},
        )


def test_regression_run_requires_selection_unless_allow_all() -> None:
    """Regression runs require an explicit selection."""
    with pytest.raises(ValidationError):
        RegressionRunRequest(owner_scope=["workspace:main"])
    request = RegressionRunRequest(
        owner_scope=["workspace:main"],
        metadata={"allow_all": True},
    )
    assert request.metadata["allow_all"] is True
