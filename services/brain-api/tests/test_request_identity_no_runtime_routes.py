from __future__ import annotations

from pathlib import Path

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container

ROOT = Path(__file__).resolve().parents[3]


def test_no_request_identity_or_production_auth_api_router_was_created() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/production_auth.py").exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/request_identity.py").exists()


def test_application_route_table_has_no_request_identity_runtime_surface() -> None:
    container = kernel_container()
    container.settings.production_auth_request_boundary_enabled = True
    app = create_app(container)
    paths = {route.path for route in app.routes if hasattr(route, "path")}
    blocked_fragments = (
        "/production-auth",
        "/auth/production",
        "/request-identity",
        "/identity/verify",
    )

    assert not any(fragment in path for path in paths for fragment in blocked_fragments)
    assert not any(path.endswith("/login") for path in paths)
    assert not any(path.endswith("/logout") for path in paths)
    assert not any(path.endswith("/callback") for path in paths)
    assert not any(path.endswith("/token") for path in paths)
    assert not any(path.endswith("/credentials") for path in paths)
    assert "securitySchemes" not in app.openapi().get("components", {})


def test_no_sdk_or_cli_request_identity_runtime_resource_exists() -> None:
    sdk_root = ROOT / "packages/aion-sdk-python/src"

    assert not list(sdk_root.rglob("*request_identity*"))
    assert not list(sdk_root.rglob("*production_auth*"))
