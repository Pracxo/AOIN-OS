"""Transport contracts for AION-248.

The installed package defines data contracts only. The uninstalled local runner
owns DNS, TLS, HTTPS, and credential header construction.
"""

from __future__ import annotations

from typing import Protocol

from aion_brain.contracts.live_provider_pilot import (
    LiveProviderRequestProjection,
    LiveProviderTransportResult,
)


class LiveProviderTransport(Protocol):
    """A transport seam for tests and the uninstalled runner."""

    def send(
        self,
        *,
        request_projection: LiveProviderRequestProjection,
        payload: dict[str, object],
    ) -> LiveProviderTransportResult:
        """Return a safe transport result projection."""
        ...
