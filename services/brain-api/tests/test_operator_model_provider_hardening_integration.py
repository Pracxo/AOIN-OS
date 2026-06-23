"""Operator integration for model provider hardening blockers."""

from __future__ import annotations

from aion_brain.contracts.model_provider_hardening import ModelProviderBlocker
from aion_brain.operator.action_center import ActionCenterService
from aion_brain.operator.repository import OperatorRepository
from tests.model_gateway_fakes import AllowPolicy
from tests.model_provider_hardening_helpers import repository


def test_operator_surfaces_provider_hardening_blockers() -> None:
    hardening_repo = repository()
    hardening_repo.save_blocker(
        ModelProviderBlocker(
            provider_blocker_id="blocker-1",
            provider_key="generic.metadata_only",
            blocker_type="raw_prompt_detected",
            severity="critical",
            status="open",
            reason="Unsafe prompt body metadata was detected.",
            recommended_action="review prompt egress preview",
        )
    )
    service = ActionCenterService(
        OperatorRepository(database_url="sqlite+pysqlite:///:memory:"),
        policy_adapter=AllowPolicy(),
        model_provider_hardening_repository=hardening_repo,
    )

    items = service.build_action_items(["workspace:main"])

    assert any(item.source_type == "model_provider_blocker" for item in items)
    assert all(item.metadata.get("provider_enabled") is False for item in items)
