from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container

ROOT = Path(__file__).resolve().parents[3]


def test_no_production_auth_api_router_was_created() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/production_auth.py").exists()


def test_application_route_table_has_no_production_auth_runtime_surface() -> None:
    app = create_app(kernel_container())
    client = TestClient(app)
    paths = {route.path for route in app.routes if hasattr(route, "path")}

    assert client.get("/health").status_code in {200, 404}
    assert not any("/production-auth" in path for path in paths)
    assert not any("/auth/production" in path for path in paths)
    assert not any("/production/oauth" in path for path in paths)
    assert not any("/production/oidc" in path for path in paths)
    assert not any("/production/saml" in path for path in paths)
    assert not any(path.endswith("/login") for path in paths)
    assert not any(path.endswith("/logout") for path in paths)
    assert not any(path.endswith("/callback") for path in paths)
    assert not any(path.endswith("/token") for path in paths)
    assert not any(path.endswith("/credentials") for path in paths)


def test_static_console_production_auth_core_evidence_is_bundled_read_only() -> None:
    demo_dir = ROOT / "operator-console-static/demo-data"
    app_js = (ROOT / "operator-console-static/app.js").read_text()

    for name in ("production-auth-core-status.json", "production-auth-runtime-hold.json"):
        text = (demo_dir / name).read_text()
        assert '"read_only": true' in text
        assert '"production_auth_core_implemented": true' in text
        assert '"production_auth_runtime_enabled": false' in text
        assert name not in app_js
