"""Fail-closed endpoint policy for the local Ollama pilot."""
from __future__ import annotations

from urllib.parse import urlsplit

ENDPOINT = "http://127.0.0.1:11434/api/chat"


def require_local_endpoint(value: str) -> None:
    parts = urlsplit(value)
    if (
        value != ENDPOINT
        or parts.scheme != "http"
        or parts.hostname != "127.0.0.1"
        or parts.port != 11434
        or parts.path != "/api/chat"
    ):
        raise ValueError("local Ollama endpoint is outside the authorized loopback policy")
