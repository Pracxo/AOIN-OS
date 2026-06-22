"""Open Policy Agent readiness boundary."""

import httpx


def check_opa(opa_url: str, timeout_seconds: float = 1.0) -> bool:
    """Return whether OPA is reachable over HTTP."""
    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            response = client.get(f"{opa_url.rstrip('/')}/health")
        return response.is_success
    except Exception:
        return False
