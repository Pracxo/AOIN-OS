"""Deterministic development bootstrap metadata."""

from typing import Any

from aion_brain.config import Settings


def build_dev_bootstrap(settings: Settings) -> dict[str, Any]:
    """Return local development actor and workspace metadata without persistence."""
    if settings.env != "development" or not settings.dev_auth_enabled:
        return {"enabled": False}
    return {
        "enabled": True,
        "actor_id": settings.default_dev_actor_id,
        "workspace_id": settings.default_dev_workspace_id,
        "security_scope": [
            f"workspace:{settings.default_dev_workspace_id}",
            f"actor:{settings.default_dev_actor_id}",
        ],
    }
