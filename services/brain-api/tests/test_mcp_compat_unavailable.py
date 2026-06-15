"""MCP compat unavailable tests."""

import importlib

from aion_brain.mcp.compat import MCPCompat


def test_mcp_compat_reports_package_unavailable(monkeypatch) -> None:
    real_import = importlib.import_module

    def fake_import(name: str):
        if name == "mcp":
            raise ModuleNotFoundError(name)
        return real_import(name)

    monkeypatch.setattr(importlib, "import_module", fake_import)
    compat = MCPCompat()

    assert compat.is_available() is False
    assert compat.availability_reason() == "package_unavailable"
