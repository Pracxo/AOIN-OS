"""Local no-op sandbox adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.config import Settings
from aion_brain.contracts.sandbox import SandboxProfile, SandboxRunRequest, SandboxRunResult


class LocalNoopSandboxAdapter:
    """Safe local adapter that never executes code."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def status(self) -> dict[str, object]:
        """Return adapter status."""
        return {
            "adapter": "local_noop",
            "enabled": True,
            "executes_code": False,
            "sandbox_execution_enabled": self._settings.sandbox_execution_enabled,
        }

    def run(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
    ) -> SandboxRunResult:
        """Return dry-run metadata only."""
        now = datetime.now(UTC)
        run_id = request.sandbox_run_id or f"sandbox-run-{uuid4().hex}"
        if request.mode == "controlled":
            return SandboxRunResult(
                sandbox_run_id=run_id,
                trace_id=request.trace_id,
                sandbox_profile_id=profile.sandbox_profile_id,
                target_type=request.target_type,
                target_id=request.target_id,
                mode=request.mode,
                status="unsupported",
                output={},
                error={"reason": "controlled_execution_not_implemented"},
                created_at=now,
                started_at=now,
                completed_at=now,
            )
        return SandboxRunResult(
            sandbox_run_id=run_id,
            trace_id=request.trace_id,
            sandbox_profile_id=profile.sandbox_profile_id,
            target_type=request.target_type,
            target_id=request.target_id,
            mode=request.mode,
            status="dry_run",
            output={
                "dry_run": True,
                "message": "Sandbox run validated. No code executed.",
                "module_code_executed": False,
                "external_calls": False,
            },
            error={},
            created_at=now,
            started_at=now,
            completed_at=now,
        )
