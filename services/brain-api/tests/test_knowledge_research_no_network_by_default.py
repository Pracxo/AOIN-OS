from __future__ import annotations

import pytest
from test_knowledge_research_fetch_adapters import valid_request

from aion_brain.knowledge_intelligence.research_adapters import (
    OperatorInvokedHttpResearchAdapter,
    ResearchAdapterDisabledError,
)


def test_no_public_network_fetch_by_default():
    adapter = OperatorInvokedHttpResearchAdapter()
    assert adapter.public_network_fetch_available is False
    with pytest.raises(ResearchAdapterDisabledError):
        adapter.fetch(valid_request())
