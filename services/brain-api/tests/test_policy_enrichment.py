"""Policy enrichment tests."""

from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.policy.enrichment import PolicyInputEnricher


def test_policy_input_enricher_adds_actor_context() -> None:
    """Policy requests receive actor context without mutating callers."""
    request = PolicyRequest(
        request_id="request-1",
        trace_id=None,
        actor_id=None,
        workspace_id=None,
        action_type="memory.retrieve",
        resource_type="memory",
        resource_id=None,
        risk_level="low",
        approval_present=False,
        requested_permissions=[],
        security_scope=[],
        context={},
    )
    context = ActorContext(
        actor_id="actor-1",
        workspace_id="workspace-1",
        roles=["viewer"],
        permissions=["memory.read"],
        security_scope=["workspace:workspace-1"],
        dev_mode=True,
    )

    enriched = PolicyInputEnricher().enrich(request, context)

    assert enriched.actor_id == "actor-1"
    assert enriched.workspace_id == "workspace-1"
    assert enriched.security_scope == ["workspace:workspace-1"]
    assert enriched.context["roles"] == ["viewer"]
    assert enriched.context["actor_context"]["actor_id"] == "actor-1"
