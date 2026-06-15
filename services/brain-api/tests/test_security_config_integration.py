"""Security baseline runtime config integration tests."""

from __future__ import annotations

from aion_brain.security_baseline.config_checker import ConfigHardeningChecker
from tests.runtime_config_fakes import services


def test_security_config_checker_uses_runtime_config_validation() -> None:
    *_, validator, _, _ = services()
    checker = ConfigHardeningChecker(config_validator=validator)

    checks = checker.check()

    assert any(check["name"] == "runtime_config_validation_passed" for check in checks)
