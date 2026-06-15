from __future__ import annotations

from aion_sdk.config import AIONClientConfig
from aion_sdk.headers import build_aion_headers


def test_config_loads_defaults() -> None:
    config = AIONClientConfig()

    assert config.base_url == "http://localhost:8080"
    assert config.timeout_seconds == 30.0
    assert config.user_agent == "aion-sdk-python/0.1.0"


def test_config_reads_env_lists(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    monkeypatch.setenv("AION_BASE_URL", "http://localhost:9999/")
    monkeypatch.setenv("AION_ACTOR_ID", "dev")
    monkeypatch.setenv("AION_WORKSPACE_ID", "main")
    monkeypatch.setenv("AION_ROLES", "owner, operator")
    monkeypatch.setenv("AION_PERMISSIONS", "kernel.status.read, trace.read")
    monkeypatch.setenv("AION_SECURITY_SCOPE", "workspace:main, actor:dev")
    monkeypatch.setenv("AION_TIMEOUT_SECONDS", "2.5")

    config = AIONClientConfig.from_env()

    assert config.base_url == "http://localhost:9999"
    assert config.actor_id == "dev"
    assert config.workspace_id == "main"
    assert config.roles == ["owner", "operator"]
    assert config.permissions == ["kernel.status.read", "trace.read"]
    assert config.security_scope == ["workspace:main", "actor:dev"]
    assert config.timeout_seconds == 2.5


def test_build_headers_skips_empty_values_and_authorization() -> None:
    config = AIONClientConfig(
        actor_id="dev",
        workspace_id="main",
        roles=["owner"],
        permissions=["kernel.status.read", ""],
        security_scope=["workspace:main"],
        trace_id="trace-1",
        correlation_id="corr-1",
        idempotency_key="idem-1",
    )

    headers = build_aion_headers(config, {"Authorization": "Bearer nope", "X-Test": "ok"})

    assert headers["X-AION-Actor-ID"] == "dev"
    assert headers["X-AION-Workspace-ID"] == "main"
    assert headers["X-AION-Roles"] == "owner"
    assert headers["X-AION-Permissions"] == "kernel.status.read"
    assert headers["X-AION-Security-Scope"] == "workspace:main"
    assert headers["X-AION-Trace-ID"] == "trace-1"
    assert headers["X-AION-Correlation-ID"] == "corr-1"
    assert headers["Idempotency-Key"] == "idem-1"
    assert headers["X-Test"] == "ok"
    assert "Authorization" not in headers

