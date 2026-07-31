from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def load_runtime():
    from aion_brain.contracts import sandboxed_capability_runtime as runtime

    return runtime


def new_service():
    runtime = load_runtime()
    service = runtime.ControlledSandboxedCapabilityRuntimeService.create_default()
    session = service.start_session("test-capability-runtime-session")
    return runtime, service, session
