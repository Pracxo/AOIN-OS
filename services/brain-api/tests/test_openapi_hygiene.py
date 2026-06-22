"""OpenAPI hygiene tests."""

from aion_brain.api_support.openapi_hygiene import OpenAPIHygieneChecker


def test_openapi_hygiene_checker_catches_missing_tags_in_fake_route() -> None:
    report = OpenAPIHygieneChecker().check(
        {"paths": {"/brain/example": {"get": {"operationId": "example"}}}}
    )

    assert report.status == "failed"
    assert any(violation["rule"] == "route_tags_required" for violation in report.violations)


def test_openapi_hygiene_checker_catches_domain_route_prefix_in_fake_schema() -> None:
    report = OpenAPIHygieneChecker().check(
        {"paths": {"/finance/example": {"get": {"operationId": "example", "tags": ["x"]}}}}
    )

    assert report.status == "failed"
    assert any(violation["rule"] == "no_domain_route_prefix" for violation in report.violations)


def test_openapi_hygiene_allows_aion_temporal_state_contract_names() -> None:
    report = OpenAPIHygieneChecker().check(
        {
            "paths": {},
            "components": {
                "schemas": {
                    "TemporalStateWindow": {},
                    "TemporalStateWindowRequest": {},
                }
            },
        }
    )

    assert report.status == "passed"
