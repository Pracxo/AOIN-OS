from __future__ import annotations

from fastapi import Request
from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from aion_brain.production_auth.request_middleware import ProductionAuthRequestIdentityMiddleware
from tests.kernel_fakes import kernel_container


def test_default_app_does_not_register_request_identity_middleware() -> None:
    app = create_app(kernel_container())
    middleware_classes = {item.cls for item in app.user_middleware}

    assert ProductionAuthRequestIdentityMiddleware not in middleware_classes
    assert app.state.aion_request_identity_boundary_present is False


def test_enabled_app_registers_observe_only_request_identity_boundary() -> None:
    container = kernel_container()
    container.settings.production_auth_request_boundary_enabled = True
    app = create_app(container)

    @app.get("/test/request-identity-state")
    def state(request: Request) -> dict[str, object]:
        identity = request.state.aion_request_identity_context
        return {
            "request_context_present": hasattr(request.state, "aion_request_context"),
            "identity_context_present": hasattr(
                request.state,
                "aion_request_identity_context",
            ),
            "request_id_match": identity.request_id
            == request.state.aion_request_context.request_id,
            "authenticated": identity.authenticated,
            "actor_id": identity.actor_id,
            "subject": identity.subject,
            "roles": list(identity.roles),
            "runtime_effect": identity.runtime_effect,
        }

    response = TestClient(app).get(
        "/test/request-identity-state",
        headers={"X-AION-Actor-ID": "legacy-actor"},
    )

    assert app.state.aion_request_identity_boundary_present is True
    assert app.state.aion_request_identity_boundary_mode == "observe_only_disabled"
    assert app.state.aion_request_identity_identity_verification_enabled is False
    assert app.state.aion_request_identity_authenticated_requests_enabled is False
    assert response.status_code == 200
    assert response.json() == {
        "request_context_present": True,
        "identity_context_present": True,
        "request_id_match": True,
        "authenticated": False,
        "actor_id": None,
        "subject": None,
        "roles": [],
        "runtime_effect": False,
    }


def test_app_factory_keeps_route_table_and_openapi_security_surface_unchanged() -> None:
    default_app = create_app(kernel_container())
    enabled_container = kernel_container()
    enabled_container.settings.production_auth_request_boundary_enabled = True
    enabled_app = create_app(enabled_container)

    default_paths = {route.path for route in default_app.routes if hasattr(route, "path")}
    enabled_paths = {route.path for route in enabled_app.routes if hasattr(route, "path")}

    assert enabled_paths == default_paths
    assert "securitySchemes" not in enabled_app.openapi().get("components", {})
