from __future__ import annotations

import pytest
from fastapi import FastAPI

from aion_brain.kernel.app_factory import create_app
from aion_brain.production_auth.request_middleware import (
    ProductionAuthRequestIdentityMiddleware,
    register_production_auth_request_identity_middleware,
)
from tests.kernel_fakes import kernel_container


def _identity_middleware_count(app: FastAPI) -> int:
    return sum(
        1
        for item in app.user_middleware
        if item.cls is ProductionAuthRequestIdentityMiddleware
    )


def test_disabled_registration_adds_zero_middleware_instances() -> None:
    app = FastAPI()

    register_production_auth_request_identity_middleware(
        app,
        boundary=None,
        enabled=False,
    )

    assert _identity_middleware_count(app) == 0


def test_enabled_registration_adds_exactly_one_and_rejects_second_attempt() -> None:
    app = FastAPI()

    register_production_auth_request_identity_middleware(
        app,
        boundary=None,
        enabled=True,
    )

    assert _identity_middleware_count(app) == 1
    with pytest.raises(RuntimeError, match="already registered"):
        register_production_auth_request_identity_middleware(
            app,
            boundary=None,
            enabled=True,
        )
    assert _identity_middleware_count(app) == 1


def test_app_factory_uses_duplicate_safe_registration_helper() -> None:
    container = kernel_container()
    container.settings.production_auth_request_boundary_enabled = True

    app = create_app(container)

    assert _identity_middleware_count(app) == 1
    assert app.state.aion_request_identity_boundary_present is True
    assert app.state.aion_request_identity_middleware_implementation == "pure_asgi"
    assert app.state.aion_request_identity_duplicate_registration_prevented is True
