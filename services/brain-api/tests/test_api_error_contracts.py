"""API error contract tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.api import AIONError, AIONErrorResponse


def test_aion_error_validates_category() -> None:
    with pytest.raises(ValidationError):
        AIONError(
            code="AION_BAD",
            category="bad",
            message="bad",
            detail={},
            retryable=False,
            created_at=datetime.now(UTC),
        )


def test_aion_error_rejects_empty_code() -> None:
    with pytest.raises(ValidationError):
        AIONError(
            code="",
            category="validation",
            message="bad",
            detail={},
            retryable=False,
            created_at=datetime.now(UTC),
        )


def test_aion_error_rejects_secret_detail_keys() -> None:
    with pytest.raises(ValidationError):
        AIONError(
            code="AION_VALIDATION_ERROR",
            category="validation",
            message="bad",
            detail={"api_key": "secret"},
            retryable=False,
            created_at=datetime.now(UTC),
        )


def test_aion_error_response_serializes() -> None:
    response = AIONErrorResponse(
        error=AIONError(
            code="AION_VALIDATION_ERROR",
            category="validation",
            message="Invalid",
            detail={"field": "name"},
            retryable=False,
            created_at=datetime.now(UTC),
        )
    )

    dumped = response.model_dump(mode="json")

    assert dumped["error"]["code"] == "AION_VALIDATION_ERROR"
    assert dumped["error"]["category"] == "validation"
