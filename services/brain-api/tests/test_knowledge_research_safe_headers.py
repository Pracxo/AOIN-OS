from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.research_policy import project_safe_response_headers


def test_safe_headers_are_projected_and_unsafe_headers_discarded():
    projected = project_safe_response_headers(
        {
            "Content-Type": "text/plain",
            "Set-Cookie": "ignored=value",
            "WWW-Authenticate": "ignored",
            "X-Trace-Id": "internal",
        }
    )
    assert projected == {"Content-Type": "text/plain"}


def test_header_newline_and_maximum_are_enforced():
    with pytest.raises(ValueError):
        project_safe_response_headers({"Content-Type": "text/plain\nbad"})
