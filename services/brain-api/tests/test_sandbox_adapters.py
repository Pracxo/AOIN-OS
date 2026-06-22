"""Sandbox adapter tests."""

import inspect

from aion_brain.contracts.sandbox import SandboxRunRequest
from aion_brain.sandbox.docker_adapter import DockerSandboxAdapter
from aion_brain.sandbox.firecracker_adapter import FirecrackerSandboxAdapter
from aion_brain.sandbox.local_noop_adapter import LocalNoopSandboxAdapter
from tests.sandbox_fakes import profile, settings


def test_local_noop_adapter_never_executes_code() -> None:
    adapter = LocalNoopSandboxAdapter(settings())
    result = adapter.run(
        SandboxRunRequest(sandbox_profile_id="sandbox-profile-1", target_type="test"),
        profile(),
    )

    assert result.status == "dry_run"
    assert result.output["module_code_executed"] is False
    assert result.output["external_calls"] is False


def test_docker_adapter_does_not_import_docker_and_returns_unsupported() -> None:
    source = inspect.getsource(DockerSandboxAdapter)
    adapter = DockerSandboxAdapter()

    result = adapter.run(
        SandboxRunRequest(sandbox_profile_id="sandbox-profile-1", target_type="test"),
        profile(),
    )

    assert "import docker" not in source
    assert adapter.status()["enabled"] is False
    assert result.status == "unsupported"


def test_firecracker_adapter_does_not_call_subprocess_and_returns_unsupported() -> None:
    source = inspect.getsource(FirecrackerSandboxAdapter)
    adapter = FirecrackerSandboxAdapter()

    result = adapter.run(
        SandboxRunRequest(sandbox_profile_id="sandbox-profile-1", target_type="test"),
        profile(),
    )

    assert "import subprocess" not in source
    assert "subprocess." not in source
    assert adapter.status()["enabled"] is False
    assert result.status == "unsupported"
