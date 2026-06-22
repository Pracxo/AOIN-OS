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


def test_config_checker_allows_dev_placeholder_compose_secret(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n"
        "  postgres:\n"
        "    environment:\n"
        "      POSTGRES_PASSWORD: aion_dev_password\n",
        encoding="utf-8",
    )
    checker = ConfigHardeningChecker(settings(), root_dir=tmp_path)

    checks = checker.check()

    assert _status(checks, "docker_compose_has_no_raw_secrets") == "passed"


def test_config_checker_blocks_raw_compose_secret(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n"
        "  postgres:\n"
        "    environment:\n"
        "      POSTGRES_PASSWORD: productionSecretValue123\n",
        encoding="utf-8",
    )
    checker = ConfigHardeningChecker(settings(), root_dir=tmp_path)

    checks = checker.check()

    assert _status(checks, "docker_compose_has_no_raw_secrets") == "failed"


def test_config_checker_reports_warning_severity_as_warning(tmp_path) -> None:  # type: ignore[no-untyped-def]
    checker = ConfigHardeningChecker(
        settings(AION_ENV="production", AION_DEV_AUTH_ENABLED=False),
        root_dir=tmp_path,
    )

    checks = checker.check()

    assert _status(checks, "production_auth_not_claimed") == "warning"


def _status(checks: list[dict[str, object]], name: str) -> object:
    return next(check["status"] for check in checks if check["name"] == name)
