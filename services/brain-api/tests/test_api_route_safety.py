"""API route safety checks."""

from fastapi.routing import APIRoute

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_no_domain_specific_route_prefix_is_added() -> None:
    app = create_app(kernel_container())
    forbidden_prefixes = (
        "/finance",
        "/trading",
        "/legal",
        "/healthcare",
        "/hr",
        "/procurement",
        "/it-automation",
    )

    paths = [route.path for route in app.routes if isinstance(route, APIRoute)]

    assert not any(path.startswith(forbidden_prefixes) for path in paths)
