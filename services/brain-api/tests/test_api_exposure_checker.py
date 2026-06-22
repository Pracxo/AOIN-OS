"""API exposure checker tests."""

from __future__ import annotations

from aion_brain.security_baseline.api_exposure import APIExposureChecker


def test_api_exposure_checker_detects_forbidden_domain_route_prefix() -> None:
    checks = APIExposureChecker().check(
        {
            "paths": {
                "/finance/example": {"get": {"tags": ["x"]}},
                "/health": {"get": {"tags": ["health"]}},
            }
        }
    )

    assert (
        next(check for check in checks if check["name"] == "no_domain_route_prefixes")["status"]
        == "failed"
    )


def test_api_exposure_checker_reports_destructive_policy_gap_as_warning() -> None:
    checks = APIExposureChecker().check(
        {
            "paths": {
                "/brain/example/{example_id}": {"delete": {"tags": ["example"]}},
                "/health": {"get": {"tags": ["health"]}},
            }
        }
    )

    assert (
        next(
            check for check in checks if check["name"] == "destructive_routes_have_policy_category"
        )["status"]
        == "warning"
    )
