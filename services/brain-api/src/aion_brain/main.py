"""FastAPI entrypoint for AION Brain."""

from aion_brain.kernel.app_factory import create_app

app = create_app()

__all__ = ["app", "create_app"]
