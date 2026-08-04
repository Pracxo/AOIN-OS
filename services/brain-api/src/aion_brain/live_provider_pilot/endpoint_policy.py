"""Endpoint policy for the single OpenAI Responses API pilot."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.live_provider_pilot import (
    ENDPOINT_HOST,
    ENDPOINT_PATH,
    ENDPOINT_SCHEME,
    HTTP_METHOD,
    LiveProviderEndpointPolicy,
    validate_endpoint,
)


def create_endpoint_policy(*, policy_id: str, created_at: datetime) -> LiveProviderEndpointPolicy:
    """Create the exact endpoint policy."""

    return LiveProviderEndpointPolicy(policy_id=policy_id, created_at=created_at)


def require_exact_endpoint(*, scheme: str, host: str, path: str, method: str) -> None:
    """Reject alternate hosts, paths, schemes, or methods."""

    validate_endpoint(scheme=scheme, host=host, path=path, method=method)


def reject_redirect(location: str | None) -> None:
    """Redirects are never followed."""

    raise ValueError("redirect response rejected")


def reject_proxy(proxy_value_present: bool) -> None:
    """Proxy inheritance is bypassed; explicit proxy attempts are rejected."""

    if proxy_value_present:
        raise ValueError("proxy use is rejected")


EXPECTED_ENDPOINT = {
    "scheme": ENDPOINT_SCHEME,
    "host": ENDPOINT_HOST,
    "path": ENDPOINT_PATH,
    "method": HTTP_METHOD,
}
