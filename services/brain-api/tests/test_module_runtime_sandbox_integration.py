"""Module runtime sandbox integration tests."""

from types import SimpleNamespace

from aion_brain.contracts.modules import CapabilityInvocationRequest
from aion_brain.modules.runtime_gateway import CapabilityRuntimeGateway
from tests.sandbox_fakes import FakePolicyAdapter


class FakeCapabilityRegistry:
    """Capability registry fake."""

    def capability_exists(self, capability_id: str) -> bool:
        return capability_id == "test.echo"


class FailingSandbox:
    """Sandbox fake that blocks runs."""

    def has_active_grant(self, **kwargs: object) -> bool:
        return True

    def run(self, request: object) -> object:
        return SimpleNamespace(status="failed", sandbox_run_id="sandbox-run-1")


def test_module_runtime_gateway_blocks_when_sandbox_validation_fails() -> None:
    gateway = CapabilityRuntimeGateway(
        module_runtime_repository=object(),
        capability_registry=FakeCapabilityRegistry(),
        policy_adapter=FakePolicyAdapter(),
        sandbox_service=FailingSandbox(),
    )

    result = gateway.invoke(
        CapabilityInvocationRequest(
            invocation_id="invoke-1",
            capability_id="test.echo",
            mode="controlled",
            approval_present=True,
            metadata={"sandbox_profile_id": "sandbox-profile-1"},
        )
    )

    assert result.status == "blocked_by_policy"
    assert result.error["reason"] == "sandbox_validation_failed"
