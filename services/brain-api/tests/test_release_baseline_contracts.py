"""Release baseline contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.release_baseline import ReleaseBaselineRequest


def test_release_baseline_request_validates_version() -> None:
    with pytest.raises(ValidationError):
        ReleaseBaselineRequest(version="", owner_scope=["workspace:main"])


def test_release_baseline_request_rejects_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        ReleaseBaselineRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            metadata={"token": "nope"},
        )
