from __future__ import annotations

import pytest
from test_knowledge_research_fetch_adapters import valid_request

from aion_brain.knowledge_intelligence.research_adapters import (
    OperatorInvokedHttpResearchAdapter,
    ResearchAdapterDisabledError,
)


def test_http_policy_adapter_is_explicit_and_network_disabled():
    adapter = OperatorInvokedHttpResearchAdapter()
    assert adapter.operator_invoked_http_adapter_policy_available is True
    assert adapter.system_http_transport_available is False
    assert adapter.public_network_fetch_available is False
    with pytest.raises(ResearchAdapterDisabledError) as exc_info:
        adapter.fetch(valid_request())
    assert exc_info.value.reason_code == "research_network_transport_unavailable"
