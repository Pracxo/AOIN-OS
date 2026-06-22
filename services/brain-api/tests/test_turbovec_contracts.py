"""TurboVec public contract tests."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from aion_brain.contracts.memory import TurboVecIndexStatus, TurboVecRebuildRequest


def test_turbovec_index_status_validates_bit_width() -> None:
    """TurboVecIndexStatus rejects unsupported bit widths."""
    with pytest.raises(ValidationError):
        TurboVecIndexStatus(
            index_id="index-1",
            index_name="default",
            adapter_name="turbovec",
            dimensions=384,
            bit_width=5,
            index_path="/tmp/index.tvindex",
            status="active",
            entry_count=0,
            available=True,
            reason=None,
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            rebuilt_at=None,
        )


def test_turbovec_rebuild_request_rejects_unsafe_index_name() -> None:
    """Index names cannot escape the configured index directory."""
    with pytest.raises(ValidationError):
        TurboVecRebuildRequest(index_name="../escape", scope=["workspace:main"])


def test_turbovec_rebuild_request_rejects_empty_scope() -> None:
    """Rebuild scope is mandatory."""
    with pytest.raises(ValidationError):
        TurboVecRebuildRequest(scope=[])


def test_turbovec_rebuild_request_rejects_invalid_time_independent_limit() -> None:
    """Rebuild limits stay bounded for local control."""
    with pytest.raises(ValidationError):
        TurboVecRebuildRequest(scope=["workspace:main"], limit=1_000_001)


def test_turbovec_index_status_rejects_secret_metadata() -> None:
    """Public index metadata cannot carry secret-like keys."""
    with pytest.raises(ValidationError):
        TurboVecIndexStatus(
            index_id="index-1",
            index_name="default",
            adapter_name="turbovec",
            dimensions=384,
            bit_width=4,
            index_path="/tmp/index.tvindex",
            status="active",
            entry_count=0,
            available=True,
            reason=None,
            metadata={"api_key": "nope"},
            created_at=datetime.now(UTC) - timedelta(seconds=1),
            updated_at=datetime.now(UTC),
            rebuilt_at=None,
        )
