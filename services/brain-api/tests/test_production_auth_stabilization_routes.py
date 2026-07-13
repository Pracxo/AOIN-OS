from __future__ import annotations

from pathlib import Path

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container

ROOT = Path(__file__).resolve().parents[3]


def test_production_auth_api_router_remains_absent() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/production_auth.py").exists()


def test_route_table_has_no_authentication_runtime_surface() -> None:
    app = create_app(kernel_container())
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    blocked_segments = {
        "login",
        "logout",
        "callback",
        "oauth",
        "oidc",
        "saml",
        "token",
        "session",
        "credential",
        "credentials",
        "production-auth",
    }

    for path in paths:
        segments = set(path.strip("/").split("/"))
        assert not (segments & blocked_segments)
        assert not path.startswith("/auth/production")
