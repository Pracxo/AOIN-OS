from __future__ import annotations

from aion_brain.knowledge_intelligence.public_research_policy import project_safe_response_headers


def test_response_headers_are_projected_safely() -> None:
    headers = project_safe_response_headers({"Content-Type": "text/plain", "Set-Cookie": "x=y"})
    assert "content-type" in headers
    assert "set-cookie" not in headers
