from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import bind_secure_actor_context
from tests.secure_runtime_test_support import (
    ALLOWED_PERMISSIONS,
    ALLOWED_ROLES,
    secure_runtime_fixture,
)


def test_actor_context_is_verified_local_operator_not_anonymous() -> None:
    fixture = secure_runtime_fixture()

    assert fixture.actor_context.actor_context.actor_type == "local_operator"
    assert fixture.actor_context.actor_context.actor_id == "operator-AION-231"
    assert fixture.actor_context.anonymous_context is False
    assert fixture.actor_context.development_simulation is False


def test_actor_context_rejects_scope_escalation() -> None:
    fixture = secure_runtime_fixture()

    with pytest.raises(ValueError, match="unknown scope"):
        bind_secure_actor_context(
            request_identity_binding=fixture.request_identity,
            allowed_roles=ALLOWED_ROLES,
            allowed_permissions=ALLOWED_PERMISSIONS,
            allowed_security_scopes=("secure-runtime:health",),
        )
