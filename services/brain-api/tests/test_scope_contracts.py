"""Scope contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.scopes import ActorContext, ScopeResolutionRequest


def test_scope_resolution_request_validates_requested_scopes() -> None:
    """Scope resolution requires requested scopes."""
    with pytest.raises(ValidationError):
        ScopeResolutionRequest(
            actor_id="actor-1",
            workspace_id="workspace-1",
            requested_scopes=[],
            action_type="memory.retrieve",
            resource_type="memory",
        )


def test_actor_context_defaults_security_scope_and_dev_mode() -> None:
    """ActorContext defaults to no implicit production scope."""
    context = ActorContext()

    assert context.security_scope == []
    assert context.dev_mode is False
