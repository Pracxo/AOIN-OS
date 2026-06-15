"""AION development identity and trace header helpers."""

from aion_sdk.config import AIONClientConfig


def _set_if_present(headers: dict[str, str], key: str, value: str | list[str] | None) -> None:
    if isinstance(value, list):
        joined = ",".join(item for item in value if item)
        if joined:
            headers[key] = joined
        return
    if value:
        headers[key] = value


def build_aion_headers(
    config: AIONClientConfig,
    extra: dict[str, str] | None = None,
) -> dict[str, str]:
    """Build AION Brain request headers without production auth secrets."""

    headers: dict[str, str] = {"User-Agent": config.user_agent}
    _set_if_present(headers, "X-AION-Actor-ID", config.actor_id)
    _set_if_present(headers, "X-AION-Workspace-ID", config.workspace_id)
    _set_if_present(headers, "X-AION-Roles", config.roles)
    _set_if_present(headers, "X-AION-Permissions", config.permissions)
    _set_if_present(headers, "X-AION-Security-Scope", config.security_scope)
    _set_if_present(headers, "X-AION-Trace-ID", config.trace_id)
    _set_if_present(headers, "X-AION-Correlation-ID", config.correlation_id)
    _set_if_present(headers, "Idempotency-Key", config.idempotency_key)
    if extra:
        for key, value in extra.items():
            if value and key.lower() != "authorization":
                headers[key] = value
    headers.pop("Authorization", None)
    return headers

