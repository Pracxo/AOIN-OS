from __future__ import annotations

from aion_brain.contracts.local_auth import DevIdentitySimulationRequest
from aion_brain.local_auth.identity import build_local_operator_identity


def test_build_local_operator_identity_is_synthetic_and_material_free() -> None:
    identity = build_local_operator_identity(
        DevIdentitySimulationRequest(
            actor_id="local.viewer",
            workspace_id="local",
            roles=["viewer"],
            owner_scope=["workspace:main"],
        )
    )

    assert identity.status == "simulated"
    assert identity.identity_source == "local_dev"
    assert identity.production_identity is False
    assert identity.credentials_present is False
    assert identity.metadata["synthetic"] is True
