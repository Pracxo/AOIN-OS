"""Optional adapter risk checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aion_brain.config import Settings, get_settings


class AdapterRiskChecker:
    """Check that optional adapters remain disabled or metadata-only by default."""

    def __init__(self, settings: Settings | None = None, *, root_dir: Path | None = None) -> None:
        self._settings = settings or get_settings()
        self._root_dir = root_dir or Path(__file__).parents[5]

    def check(self) -> list[dict[str, Any]]:
        """Return adapter risk checks."""
        return [
            _check("turbovec_optional", not self._settings.turbovec_enabled, "adapter"),
            _check("graphiti_optional", not self._settings.graphiti_enabled, "adapter"),
            _check("mcp_optional", not self._settings.mcp_enabled, "mcp"),
            _check("temporal_optional", not self._settings.temporal_enabled, "adapter"),
            _check(
                "litellm_optional",
                self._settings.model_gateway_adapter != "litellm",
                "model_gateway",
            ),
            _check(
                "minio_optional",
                self._settings.default_object_store != "minio",
                "adapter",
            ),
            _check(
                "langfuse_optional",
                self._settings.observability_adapter != "langfuse",
                "observability",
            ),
            _check(
                "docker_sandbox_disabled",
                not self._settings.sandbox_docker_enabled,
                "sandbox",
            ),
            _check(
                "firecracker_sandbox_disabled",
                not self._settings.sandbox_firecracker_enabled,
                "sandbox",
            ),
            _check(
                "external_connectors_metadata_only",
                self._settings.connector_registry_enabled,
                "connector",
                severity="medium",
            ),
            _check(
                "no_provider_sdk_objects_in_public_contracts",
                not _contracts_contain_provider_objects(self._root_dir),
                "api",
            ),
        ]


def _check(
    name: str,
    passed: bool,
    category: str,
    *,
    severity: str = "high",
) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "status": "passed" if passed else "failed",
        "severity": severity,
        "message": f"{name} {'passed' if passed else 'failed'}.",
        "details": {},
    }


def _contracts_contain_provider_objects(root_dir: Path) -> bool:
    contracts = root_dir / "services" / "brain-api" / "src" / "aion_brain" / "contracts"
    if not contracts.exists():
        return False
    provider_terms = ("OpenAIObject", "AnthropicMessage", "LiteLLMResponse", "ProviderResponse")
    for path in contracts.rglob("*.py"):
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if any(term in text for term in provider_terms):
            return True
    return False
