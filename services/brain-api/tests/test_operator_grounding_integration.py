from __future__ import annotations

from types import SimpleNamespace

from aion_brain.operator.action_center import ActionCenterService
from tests.operator_fakes import SCOPE, AllowPolicy, FakeTelemetry, repository


class FakeGroundingVerifier:
    def list_verification_runs(self, limit: int = 100) -> list[object]:
        return [
            SimpleNamespace(
                grounding_verification_id="grounding-verification-1",
                trace_id="trace-1",
                status="failed",
                coverage_score=0.0,
                owner_scope=SCOPE,
            )
        ][:limit]


def test_action_center_surfaces_failed_grounding_verification() -> None:
    service = ActionCenterService(
        repository(),
        AllowPolicy(),
        FakeTelemetry(),
        grounding_verifier=FakeGroundingVerifier(),
    )

    items = service.build_action_items(SCOPE)

    assert items[0].recommended_action == "review_grounding_verification"
