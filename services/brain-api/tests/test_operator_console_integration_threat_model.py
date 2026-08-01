from __future__ import annotations

from operator_console_integration_test_support import operator_auth


def test_operator_console_threat_model_records_required_threats():
    threats = set(operator_auth()["threat_model"])
    expected = {
        "DNS rebinding",
        "cross-site request forgery",
        "model output triggering execution",
        "production-write activation",
        "Git mutation",
        "model training",
    }
    for item in expected:
        assert item in threats
