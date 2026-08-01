from __future__ import annotations

from operator_console_integration_test_support import operator_auth


def test_operator_console_security_headers_exact():
    headers = operator_auth()["security_headers"]
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert "unsafe-eval" not in headers["Content-Security-Policy"]
    assert "connect-src 'self'" in headers["Content-Security-Policy"]
