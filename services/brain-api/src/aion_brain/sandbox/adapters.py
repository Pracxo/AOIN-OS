"""Sandbox adapter boundary."""

from __future__ import annotations

from typing import Any, Protocol

from aion_brain.contracts.sandbox import SandboxProfile, SandboxRunRequest, SandboxRunResult


class SandboxAdapter(Protocol):
    """Boundary for future sandbox engines."""

    def status(self) -> dict[str, Any]:
        """Return adapter status metadata."""

    def run(
        self,
        request: SandboxRunRequest,
        profile: SandboxProfile,
    ) -> SandboxRunResult:
        """Return a sandbox run result without leaking engine types."""
