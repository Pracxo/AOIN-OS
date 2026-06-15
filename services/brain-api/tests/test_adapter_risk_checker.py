"""Adapter risk checker tests."""

from __future__ import annotations

from aion_brain.security_baseline.adapter_risk import AdapterRiskChecker
from tests.security_fakes import settings


def test_adapter_risk_checker_detects_mcp_enabled_by_default(tmp_path) -> None:  # type: ignore[no-untyped-def]
    checks = AdapterRiskChecker(settings(AION_MCP_ENABLED=True), root_dir=tmp_path).check()

    assert next(check for check in checks if check["name"] == "mcp_optional")["status"] == "failed"
