from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import response_policy_decision


def test_compressed_response_is_rejected() -> None:
    with pytest.raises(ValueError):
        response_policy_decision(
            status_code=200,
            method="GET",
            headers=(("Content-Encoding", "gzip"), ("Content-Type", "text/plain")),
            maximum_response_bytes=100,
            allowed_content_types=("text/plain",),
        )
