"""Model gateway autonomy integration tests."""

from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.model_gateway_fakes import gateway_request, model_gateway_service


def test_model_gateway_blocks_completion_when_autonomy_denies() -> None:
    """Model completion is gated by autonomy before provider execution."""
    service, _repo, _policy, _telemetry = model_gateway_service()
    service._autonomy_governor = FakeAutonomyGovernor(allow=False)  # noqa: SLF001

    response = service.complete(gateway_request())

    assert response.status == "blocked_by_policy"
    assert response.usage.status == "blocked"
