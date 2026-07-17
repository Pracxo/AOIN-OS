"""AION-160 RequestContext correlation projection tests."""

from datetime import UTC, datetime

from aion_brain.contracts.actor_context_resolution import ActorContextResolutionInput
from aion_brain.contracts.api import RequestContext
from aion_brain.production_auth.actor_context import ProductionAuthActorContextResolver


def test_only_trace_and_correlation_are_projected_from_request_context() -> None:
    request_context = RequestContext(
        request_id="request-1",
        trace_id="trace-1",
        correlation_id="corr-1",
        idempotency_key="idempotency-1",
        actor_id="root",
        workspace_id="system",
        method="POST",
        path="/brain/events",
        started_at=datetime.now(UTC),
        metadata={"api_version": "v0.1"},
    )
    bundle = ProductionAuthActorContextResolver().resolve(
        ActorContextResolutionInput(
            request_id=request_context.request_id,
            trace_id=request_context.trace_id,
            correlation_id=request_context.correlation_id,
            metadata={
                "request_context_actor_ignored": True,
                "request_context_workspace_ignored": True,
            },
        )
    )

    assert bundle.actor_context.trace_id == "trace-1"
    assert bundle.actor_context.correlation_id == "corr-1"
    assert bundle.actor_context.actor_id is None
    assert bundle.actor_context.workspace_id is None
    assert bundle.actor_context.permissions == []
    assert "request_context_identity_metadata_ignored" in bundle.reason_codes
