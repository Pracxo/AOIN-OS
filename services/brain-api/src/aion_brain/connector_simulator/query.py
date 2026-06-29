"""Connector simulator query helpers."""

from __future__ import annotations

from typing import Any


class ConnectorSimulatorQueryService:
    """Expose stateless connector simulator status and query summaries."""

    def __init__(self, *, settings: object | None = None) -> None:
        self._settings = settings

    def status(self, scope: list[str]) -> dict[str, Any]:
        """Return safe simulator status for one scope."""

        return {
            "status": "enabled",
            "read_only": True,
            "synthetic_only": True,
            "owner_scope": scope,
            "connector_simulator_enabled": bool(
                getattr(self._settings, "connector_simulator_enabled", True)
            ),
            "connector_dry_run_simulation_enabled": bool(
                getattr(self._settings, "connector_dry_run_simulation_enabled", True)
            ),
            "connector_replay_fixtures_enabled": bool(
                getattr(self._settings, "connector_replay_fixtures_enabled", True)
            ),
            "connector_policy_readiness_enabled": bool(
                getattr(self._settings, "connector_policy_readiness_enabled", True)
            ),
            "connector_simulator_external_calls_enabled": False,
            "connector_simulator_credentials_enabled": False,
            "connector_simulator_tokens_enabled": False,
            "connector_simulator_runtime_activation_enabled": False,
            "connector_runtime_enabled": False,
        }

    def query(self, payload: dict[str, Any], scope: list[str]) -> dict[str, Any]:
        """Return a deterministic query summary without stored state."""

        return {
            "status": "passed",
            "read_only": True,
            "synthetic_only": True,
            "owner_scope": scope,
            "requested": {
                "connector_key": payload.get("connector_key", "mock.local.preview"),
                "include_findings": bool(payload.get("include_findings", True)),
            },
            "external_calls_made": False,
            "credentials_used": False,
            "tokens_used": False,
            "connector_runtime_enabled": False,
        }


__all__ = ["ConnectorSimulatorQueryService"]
