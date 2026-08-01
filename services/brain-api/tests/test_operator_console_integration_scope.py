from __future__ import annotations

from operator_console_integration_test_support import operator_auth

EXPECTED_SCOPE = (
    "authenticated-local-loopback-same-origin-operator-console-bridge-secure-session-"
    "bootstrap-live-read-projection-explicit-model-simulation-explicit-reference-"
    "capability-execution-synthetic-connector-preview-request-nonce-origin-host-csp-"
    "kill-switch-audit-receipt-integrity-integrated-pilot-no-external-effect-core"
)


def test_operator_console_authorization_scope_exact():
    assert operator_auth()["authorization_scope"] == EXPECTED_SCOPE
