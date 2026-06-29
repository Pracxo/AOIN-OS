"""FastAPI entrypoint for AION Brain.

Routes, including disabled connector-runtime preview routes, are assembled by
the application factory.
"""

from aion_brain.kernel.app_factory import create_app

app = create_app()

__all__ = ["app", "create_app"]
