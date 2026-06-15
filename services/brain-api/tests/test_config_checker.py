"""Config hardening checker tests."""

from __future__ import annotations

from aion_brain.security_baseline.config_checker import ConfigHardeningChecker
from tests.security_fakes import settings


def test_config_checker_detects_external_models_enabled_by_default(tmp_path) -> None:  # type: ignore[no-untyped-def]
    checker = ConfigHardeningChecker(
        settings(AION_MODEL_GATEWAY_ENABLED=True),
        root_dir=tmp_path,
    )

    checks = checker.check()

    assert _status(checks, "external_models_disabled_by_default") == "failed"


def test_config_checker_detects_stacktrace_exposure_enabled(tmp_path) -> None:  # type: ignore[no-untyped-def]
    checker = ConfigHardeningChecker(
        settings(AION_API_STACKTRACE_EXPOSED=True),
        root_dir=tmp_path,
    )

    checks = checker.check()

    assert _status(checks, "api_stacktrace_exposed_false") == "failed"


def _status(checks: list[dict[str, object]], name: str) -> object:
    return next(check["status"] for check in checks if check["name"] == name)
