from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.config import Settings
from aion_brain.contracts.production_auth import ProductionAuthCoreConfig


def test_production_auth_settings_default_false_for_new_boundaries() -> None:
    settings = Settings(_env_file=None)

    for name in _new_boundary_settings():
        assert getattr(settings, name) is False


def test_production_auth_config_maps_existing_settings_fail_closed() -> None:
    settings = Settings(_env_file=None)
    config = ProductionAuthCoreConfig.from_settings(settings)

    assert config.runtime_enabled is False
    assert config.login_endpoint_enabled is False
    assert config.logout_endpoint_enabled is False
    assert config.callback_endpoint_enabled is False
    assert config.external_identity_provider_enabled is False


@pytest.mark.parametrize(
    "env_key",
    [
        "AION_PRODUCTION_AUTH_ENABLED",
        "AION_AUTH_RUNTIME_ENABLED",
        "AION_AUTH_RUNTIME_LOGIN_ENDPOINT_ENABLED",
        "AION_AUTH_RUNTIME_LOGOUT_ENDPOINT_ENABLED",
        "AION_AUTH_RUNTIME_CREDENTIALS_ENABLED",
        "AION_AUTH_RUNTIME_TOKEN_ISSUANCE_ENABLED",
        "AION_AUTH_RUNTIME_COOKIE_ISSUANCE_ENABLED",
        "AION_AUTH_RUNTIME_SESSION_PERSISTENCE_ENABLED",
        "AION_AUTH_CREDENTIALS_ENABLED",
        "AION_AUTH_SESSIONS_ENABLED",
        "AION_EXTERNAL_IDENTITY_PROVIDER_ENABLED",
        "AION_PRODUCTION_AUTH_CALLBACK_ENDPOINT_ENABLED",
        "AION_PRODUCTION_AUTH_PASSWORD_STORAGE_ENABLED",
        "AION_PRODUCTION_AUTH_TOKEN_STORAGE_ENABLED",
        "AION_PRODUCTION_AUTH_SESSION_CREATION_ENABLED",
        "AION_PRODUCTION_AUTH_COOKIE_SESSION_PERSISTENCE_ENABLED",
        "AION_PRODUCTION_AUTH_OAUTH_RUNTIME_ENABLED",
        "AION_PRODUCTION_AUTH_OIDC_RUNTIME_ENABLED",
        "AION_PRODUCTION_AUTH_SAML_RUNTIME_ENABLED",
        "AION_PRODUCTION_AUTH_EXTERNAL_CALLS_ENABLED",
        "AION_PRODUCTION_AUTH_NETWORK_CLIENT_ENABLED",
        "AION_PRODUCTION_AUTH_PROVIDER_SDK_ENABLED",
    ],
)
def test_production_auth_config_rejects_any_runtime_setting_true(env_key: str) -> None:
    settings = Settings(_env_file=None, **{env_key: True})

    with pytest.raises(ValidationError):
        ProductionAuthCoreConfig.from_settings(settings)


def test_no_secret_bearing_production_auth_settings_were_added() -> None:
    field_names = {
        name
        for name in Settings.model_fields
        if name.startswith("production_auth_")
    }
    blocked = {"secret", "client_secret", "api_key", "private_key", "issuer_key"}

    assert field_names
    assert not any(any(marker in name for marker in blocked) for name in field_names)


def _new_boundary_settings() -> tuple[str, ...]:
    return (
        "production_auth_core_runtime_enabled",
        "production_auth_callback_endpoint_enabled",
        "production_auth_password_storage_enabled",
        "production_auth_token_storage_enabled",
        "production_auth_session_creation_enabled",
        "production_auth_cookie_session_persistence_enabled",
        "production_auth_oauth_runtime_enabled",
        "production_auth_oidc_runtime_enabled",
        "production_auth_saml_runtime_enabled",
        "production_auth_external_calls_enabled",
        "production_auth_network_client_enabled",
        "production_auth_provider_sdk_enabled",
    )
