"""AION-160 no runtime auth surface tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_aion160_does_not_add_public_auth_routes_or_sdk_runtime_surface() -> None:
    assert not (ROOT / "services/brain-api/src/aion_brain/api/production_auth.py").exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/request_identity.py").exists()
    assert not (ROOT / "services/brain-api/src/aion_brain/api/actor_context.py").exists()


def test_resolver_core_does_not_access_raw_http_material() -> None:
    source = (
        ROOT / "services/brain-api/src/aion_brain/production_auth/actor_context.py"
    ).read_text()

    assert "request.headers" not in source
    assert "request.cookies" not in source
    assert "request.query_params" not in source
    assert "request.body" not in source
    assert "Request" not in source
