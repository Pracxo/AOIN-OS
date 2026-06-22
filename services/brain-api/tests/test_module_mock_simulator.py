"""Module mock simulator tests."""

from __future__ import annotations

import pytest

from aion_brain.api_support.errors import AIONPolicyDeniedException
from aion_brain.module_mock_runtime import ModuleMockRuntimeRepository, ModuleMockSimulator
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import (
    DenyPolicy,
    FakeExternalService,
    FakeTelemetry,
    bound_module,
    invocation_request,
    repository,
    settings,
)


def _simulator(
    repo: ModuleMockRuntimeRepository,
    *,
    policy: object | None = None,
    telemetry: FakeTelemetry | None = None,
) -> tuple[ModuleMockSimulator, str]:
    binding_services, _slot_id, binding_id = bound_module()
    return (
        ModuleMockSimulator(
            repo,
            policy or AllowPolicy(),
            module_binding_repository=binding_services["repository"],
            telemetry_service=telemetry,
            notification_router=FakeExternalService(),
            settings=settings(),
        ),
        binding_id,
    )


def test_module_mock_simulator_passes_schema_echo_case() -> None:
    repo = repository()
    simulator, binding_id = _simulator(repo)

    run = simulator.invoke(invocation_request(binding_id))

    assert run.status == "passed"
    assert run.output is not None
    assert run.output.redacted_output_payload["synthetic"] is True
    assert run.output.redacted_output_payload["generated_by"] == "aion.module_mock_runtime"
    assert run.activation_allowed is False
    assert run.execution_allowed is False
    assert run.external_calls_made is False
    assert run.code_loaded is False


def test_module_mock_simulator_generates_generic_knowledge_answer() -> None:
    repo = repository()
    simulator, binding_id = _simulator(repo)

    run = simulator.invoke(invocation_request(binding_id, invocation_type="mock_answer"))

    assert run.output is not None
    assert (
        run.output.redacted_output_payload["answer"]
        == "Synthetic answer from metadata-only module mock runtime."
    )
    assert run.output.redacted_output_payload["shape"] == {"type": "object", "synthetic": True}


def test_module_mock_simulator_blocks_unsafe_missing_binding_without_execution() -> None:
    repo = repository()
    simulator = ModuleMockSimulator(repo, AllowPolicy(), settings=settings())

    run = simulator.invoke(invocation_request("missing-binding"))

    assert run.status == "blocked"
    assert run.findings[0].finding_type == "missing_binding"
    assert run.activation_allowed is False
    assert run.execution_allowed is False


def test_module_mock_simulator_does_not_call_external_service_or_load_code() -> None:
    repo = repository()
    simulator, binding_id = _simulator(repo)

    run = simulator.invoke(invocation_request(binding_id, create_notifications=False))

    assert run.result["capability_executed"] is False
    assert run.result["source_records_mutated"] is False
    assert run.code_loaded is False


def test_module_mock_simulator_policy_deny_blocks_invocation() -> None:
    repo = repository()
    simulator, binding_id = _simulator(repo, policy=DenyPolicy())

    with pytest.raises(AIONPolicyDeniedException):
        simulator.invoke(invocation_request(binding_id))
