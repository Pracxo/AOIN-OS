"""Configuration helpers for the disabled production-auth core."""

from __future__ import annotations

from aion_brain.contracts.production_auth import ProductionAuthCoreConfig


def production_auth_core_config_from_settings(settings: object) -> ProductionAuthCoreConfig:
    """Construct the fail-closed production-auth core config from Settings."""

    return ProductionAuthCoreConfig.from_settings(settings)


__all__ = ["production_auth_core_config_from_settings"]
