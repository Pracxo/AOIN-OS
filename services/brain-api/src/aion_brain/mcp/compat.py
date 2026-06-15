"""Compatibility boundary for optional MCP SDK APIs."""

from __future__ import annotations

import importlib
from typing import Any, cast

from aion_brain.contracts.mcp import MCPServerRecord, MCPToolDescriptor


class MCPCompat:
    """Load optional MCP SDKs without leaking SDK objects outside this boundary."""

    def __init__(self) -> None:
        self._module: Any | None = None
        self._checked = False
        self._reason: str | None = None

    def is_available(self) -> bool:
        """Return whether an MCP SDK module can be imported."""
        return self._load_module() is not None

    def availability_reason(self) -> str | None:
        """Return why the MCP SDK is unavailable."""
        self._load_module()
        return self._reason

    def create_client(self, server: MCPServerRecord) -> Any:
        """Create a client through known MCP SDK constructor shapes."""
        module = self._require_module()
        client_class = _first_present(module, ("Client", "MCPClient", "Session"))
        if client_class is None:
            raise RuntimeError("mcp_api_incompatible:client_class_missing")
        try:
            return client_class(server.endpoint_ref, **server.config)
        except TypeError:
            try:
                return client_class(server.endpoint_ref)
            except TypeError:
                try:
                    return client_class(**server.config)
                except TypeError as exc:
                    raise RuntimeError("mcp_api_incompatible:client_constructor") from exc

    def list_tools(self, client: Any, server: MCPServerRecord) -> list[MCPToolDescriptor]:
        """List tools through known MCP client method shapes."""
        method = _first_callable(client, ("list_tools", "tools"))
        if method is None:
            raise RuntimeError("mcp_api_incompatible:list_tools_missing")
        raw = method()
        return [_tool_descriptor(item) for item in _as_list(raw)]

    def call_tool(
        self,
        client: Any,
        server: MCPServerRecord,
        tool_name: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Call one tool through known MCP client method shapes."""
        method = _first_callable(client, ("call_tool", "invoke_tool", "invoke"))
        if method is None:
            raise RuntimeError("mcp_api_incompatible:call_tool_missing")
        try:
            raw = method(tool_name, payload)
        except TypeError:
            raw = method(name=tool_name, arguments=payload)
        if isinstance(raw, dict):
            return dict(raw)
        return {"result": raw}

    def close(self, client: Any) -> None:
        """Close an SDK client/session when supported."""
        method = _first_callable(client, ("close", "disconnect", "shutdown"))
        if method is not None:
            method()

    def _load_module(self) -> Any | None:
        if self._checked:
            return self._module
        self._checked = True
        try:
            self._module = importlib.import_module("mcp")
            self._reason = None
        except Exception:
            self._module = None
            self._reason = "package_unavailable"
        return self._module

    def _require_module(self) -> Any:
        module = self._load_module()
        if module is None:
            raise RuntimeError("mcp_package_unavailable")
        return module


def _first_present(target: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        value = getattr(target, name, None)
        if value is not None:
            return value
    return None


def _first_callable(target: Any, names: tuple[str, ...]) -> Any | None:
    for name in names:
        value = getattr(target, name, None)
        if callable(value):
            return value
    return None


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    tools = getattr(value, "tools", None)
    if isinstance(tools, list):
        return tools
    return []


def _tool_descriptor(raw: Any) -> MCPToolDescriptor:
    if isinstance(raw, MCPToolDescriptor):
        return raw
    if isinstance(raw, dict):
        return MCPToolDescriptor(
            name=str(raw.get("name", "")),
            description=str(raw.get("description", "")),
            input_schema=cast(dict[str, Any], raw.get("input_schema") or raw.get("schema") or {}),
            output_schema=cast(dict[str, Any] | None, raw.get("output_schema")),
            annotations=cast(dict[str, Any], raw.get("annotations") or {}),
            metadata=cast(dict[str, Any], raw.get("metadata") or {}),
        )
    return MCPToolDescriptor(
        name=str(getattr(raw, "name", "")),
        description=str(getattr(raw, "description", "")),
        input_schema=cast(dict[str, Any], getattr(raw, "input_schema", {}) or {}),
        output_schema=cast(dict[str, Any] | None, getattr(raw, "output_schema", None)),
        annotations=cast(dict[str, Any], getattr(raw, "annotations", {}) or {}),
        metadata=cast(dict[str, Any], getattr(raw, "metadata", {}) or {}),
    )
