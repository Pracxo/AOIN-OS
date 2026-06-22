"""Graphiti contract validation tests."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.graph import (
    GraphitiConfigStatus,
    GraphitiEpisodeRequest,
    GraphitiSyncRequest,
    GraphMemoryAdapterStatus,
)


def test_graphiti_config_rejects_unsafe_name_and_secret_endpoint() -> None:
    """Graphiti config status must stay safe and secret-free."""
    with pytest.raises(ValidationError):
        GraphitiConfigStatus(
            graphiti_config_id="graphiti-unsafe",
            config_name="../unsafe",
            adapter_name="graphiti",
            status="active",
            backend_type="unknown",
            endpoint_ref=None,
            available=True,
            reason=None,
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_health_check_at=None,
        )
    with pytest.raises(ValidationError):
        GraphitiConfigStatus(
            graphiti_config_id="graphiti-default",
            config_name="default",
            adapter_name="graphiti",
            status="active",
            backend_type="unknown",
            endpoint_ref="api_token_ref",
            available=True,
            reason=None,
            metadata={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            last_health_check_at=None,
        )


def test_graphiti_episode_rejects_domain_source_blank_content_and_secret_metadata() -> None:
    """Episode contracts reject domain terms, blank content, and secret-like keys."""
    base = {
        "episode_id": None,
        "trace_id": "trace-1",
        "source_type": "event",
        "source_id": "event-1",
        "content": "generic episode",
        "scope": ["workspace:main"],
        "observed_at": datetime.now(UTC),
        "metadata": {},
    }
    for update in (
        {"source_type": "finance"},
        {"content": "   "},
        {"metadata": {"api_key": "not-allowed"}},
    ):
        with pytest.raises(ValidationError):
            GraphitiEpisodeRequest(**{**base, **update})


def test_graphiti_sync_request_requires_safe_scope_and_limit() -> None:
    """Sync requests keep traversal scoped and bounded."""
    with pytest.raises(ValidationError):
        GraphitiSyncRequest(config_name="default", scope=[], limit=10)
    with pytest.raises(ValidationError):
        GraphitiSyncRequest(config_name="default", scope=["workspace:main"], limit=0)
    with pytest.raises(ValidationError):
        GraphitiSyncRequest(config_name="../default", scope=["workspace:main"], limit=10)


def test_graph_adapter_status_rejects_secret_metadata() -> None:
    """Adapter statuses must not expose secret-like metadata."""
    with pytest.raises(ValidationError):
        GraphMemoryAdapterStatus(
            adapter_name="graphiti",
            active=False,
            available=False,
            default=False,
            reason="unavailable",
            metadata={"password": "not-allowed"},
        )
