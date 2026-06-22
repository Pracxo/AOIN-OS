"""Docker sandbox placeholder adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.sandbox import SandboxProfile, SandboxRunRequest, SandboxRunResult


class DockerSandboxAdapter:
    """Docker sandbox execution is planned for a future task.

    AION contracts must remain independent of Docker internals.
    """

    def status(self) -> dict[str, object]:
        """Return disabled placeholder status."""
        return {"adapter": "docker", "enabled": False, "reason": "not_implemented"}

    def run(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
    ) -> SandboxRunResult:
        """Return unsupported without importing or calling Docker."""
        now = datetime.now(UTC)
        return SandboxRunResult(
            sandbox_run_id=request.sandbox_run_id or f"sandbox-run-{uuid4().hex}",
            trace_id=request.trace_id,
            sandbox_profile_id=profile.sandbox_profile_id,
            target_type=request.target_type,
            target_id=request.target_id,
            mode=request.mode,
            status="unsupported",
            output={},
            error={"reason": "docker_sandbox_not_implemented"},
            created_at=now,
            started_at=now,
            completed_at=now,
        )
