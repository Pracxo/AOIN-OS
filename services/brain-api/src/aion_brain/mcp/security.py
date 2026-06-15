"""Security helpers for the optional MCP boundary."""

from typing import Any

from aion_brain.config import Settings
from aion_brain.contracts.mcp import MCPServerRecord

_SECRET_KEYS = {"api_key", "apikey", "secret", "token", "password", "private_key"}
_SHELL_CONTROL_MARKERS = (";", "&&", "||", "|", "`", "$(", ">", "<")


def validate_mcp_server_security(server: MCPServerRecord, settings: Settings) -> list[str]:
    """Return security block reasons without making network or subprocess calls."""
    reasons: list[str] = []
    if not settings.mcp_enabled:
        reasons.append("mcp_disabled")
    if server.transport_type in {"http", "sse"} and not settings.mcp_allow_network:
        reasons.append("mcp_network_disabled")
    if server.transport_type == "stdio" and not settings.mcp_allow_stdio:
        reasons.append("mcp_stdio_disabled")
    if server.transport_type == "stdio":
        values = [server.endpoint_ref or ""]
        values.extend(_string_values(server.config))
        if any(contains_shell_control_chars(value) for value in values):
            reasons.append("mcp_stdio_shell_control_rejected")
    try:
        reject_secret_like_config(server.config)
    except ValueError:
        reasons.append("mcp_secret_config_rejected")
    return reasons


def contains_shell_control_chars(value: str) -> bool:
    """Return whether a string contains blocked shell control markers."""
    return any(marker in value for marker in _SHELL_CONTROL_MARKERS)


def sanitize_mcp_tool_name(name: str) -> str:
    """Return a stable generic tool name segment."""
    cleaned = []
    for character in name.strip().lower():
        if character.isalnum():
            cleaned.append(character)
        elif character in {"_", "-", ".", " "}:
            cleaned.append("-")
    collapsed = "-".join(part for part in "".join(cleaned).split("-") if part)
    return collapsed or "tool"


def reject_secret_like_config(config: dict[str, Any]) -> None:
    """Reject secret-like keys recursively."""
    _reject_secret_like_config(config)


def _reject_secret_like_config(value: object) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if normalized in _SECRET_KEYS:
                raise ValueError("config must not contain secret-like keys")
            _reject_secret_like_config(nested)
    elif isinstance(value, list):
        for item in value:
            _reject_secret_like_config(item)


def _string_values(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in _string_values(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in _string_values(nested)]
    return []
