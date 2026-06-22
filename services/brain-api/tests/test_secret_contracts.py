"""Secret reference contract tests."""

import pytest
from pydantic import ValidationError

from tests.sandbox_fakes import secret_request


def test_secret_ref_rejects_raw_secret_like_external_ref() -> None:
    with pytest.raises(ValidationError):
        secret_request(external_ref="sk-test-secret-material")


def test_secret_ref_rejects_secret_like_metadata() -> None:
    with pytest.raises(ValidationError):
        secret_request(metadata={"api_token": "metadata-only"})
