"""Kernel contract validation tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.kernel import KernelAdapterConfig, KernelSelfTestRequest


def test_kernel_adapter_config_rejects_blank_and_secret_metadata() -> None:
    with pytest.raises(ValidationError):
        KernelAdapterConfig(
            runtime_adapter=" ",
            semantic_memory_adapter="in_memory",
            graph_memory_adapter="in_memory",
            model_gateway_adapter="deterministic",
            policy_adapter="local",
            object_store_adapter="local",
            observability_adapter="local",
            module_runtime_adapters=["local_internal"],
            evaluation_adapters=["local"],
        )
    with pytest.raises(ValidationError):
        KernelAdapterConfig(
            runtime_adapter="local",
            semantic_memory_adapter="in_memory",
            graph_memory_adapter="in_memory",
            model_gateway_adapter="deterministic",
            policy_adapter="local",
            object_store_adapter="local",
            observability_adapter="local",
            module_runtime_adapters=["local_internal"],
            evaluation_adapters=["local"],
            metadata={"api_token": "not-allowed"},
        )


def test_kernel_self_test_requires_scope() -> None:
    with pytest.raises(ValidationError):
        KernelSelfTestRequest(scope=[])
