from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import (
    fixed_request_headers,
    validate_no_operator_headers,
)


def test_request_headers_are_fixed_and_credential_free() -> None:
    headers = fixed_request_headers(("text/plain",))
    assert headers["Accept-Encoding"] == "identity"
    assert "Authorization" not in headers
    with pytest.raises(ValueError):
        validate_no_operator_headers({"Cookie": "x=y"})
