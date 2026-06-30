from __future__ import annotations

from aion_brain.connector_policy.denials import ConnectorPolicyDenialService


def test_connector_policy_denials_cover_future_runtime_actions() -> None:
    service = ConnectorPolicyDenialService()

    assert service.denial_for("connector.runtime.enable") is not None
    assert service.denial_for("connector.external.call") is not None
    assert service.denial_for("connector_policy.dry_run") is None
    assert all(
        service.denial_for(action)["runtime_allowed"] is False
        for action in service.denied_actions()
        if service.denial_for(action) is not None
    )

