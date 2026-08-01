from __future__ import annotations

from operator_console_integration_test_support import load_json


def test_operator_console_route_manifest_exact():
    route = load_json("examples/secure-runtime-integration/operator-console-route-manifest.json")
    expected_methods = ["GET", "GET", "GET", "GET", "GET", "POST", "POST", "POST", "POST", "POST"]
    expected_paths = [
        "/aion/local/v1/bootstrap",
        "/aion/local/v1/status",
        "/aion/local/v1/health",
        "/aion/local/v1/observability",
        "/aion/local/v1/audit",
        "/aion/local/v1/model/simulate",
        "/aion/local/v1/capability/execute",
        "/aion/local/v1/connector/simulate",
        "/aion/local/v1/kill",
        "/aion/local/v1/session/close",
    ]
    assert [item["method"] for item in route["routes"]] == expected_methods
    assert [item["path"] for item in route["routes"]] == expected_paths
    assert route["rules"]["dynamic_path_registration_enabled"] is False
    assert route["rules"]["cors_wildcard_enabled"] is False
