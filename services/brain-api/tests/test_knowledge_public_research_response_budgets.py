from __future__ import annotations

import pytest

from aion_brain.knowledge_intelligence.public_research_policy import validate_response_body_size


def test_response_size_budget_fails_closed() -> None:
    with pytest.raises(ValueError):
        validate_response_body_size(
            11, maximum_response_bytes=10, total_transfer_bytes=0, maximum_total_transfer_bytes=100
        )
