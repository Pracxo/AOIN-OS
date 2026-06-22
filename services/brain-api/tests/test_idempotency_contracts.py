"""Idempotency contract tests."""

import pytest

from aion_brain.contracts.idempotency import IdempotencyRecord


def test_idempotency_record_validates_status() -> None:
    """Idempotency status is constrained."""
    with pytest.raises(ValueError):
        IdempotencyRecord(
            idempotency_key="idem-1",
            route="/brain/commands",
            request_hash="hash",
            status="unknown",  # type: ignore[arg-type]
        )
