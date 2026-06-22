"""Module package validator tests."""

from aion_brain.contracts.module_developer import (
    CapabilityCertificationCheck,
    ModulePackageCreateRequest,
)
from aion_brain.module_developer.validator import ModulePackageValidator
from tests.module_developer_fakes import manifest, package_request


def _failed_ids(checks: list[CapabilityCertificationCheck]) -> set[str]:
    return {check.check_id for check in checks if check.status == "failed"}


def test_validator_catches_missing_capability_schema() -> None:
    bad = manifest(capabilities=[{"capability_id": "generic.example.bad"}])

    checks = ModulePackageValidator().validate_manifest(bad)

    assert "generic.example.bad_input_schema_dict" in _failed_ids(checks)


def test_validator_catches_unsupported_risk_level() -> None:
    bad_capability = dict(manifest().capabilities[0])
    bad_capability["risk_level"] = "unknown"

    checks = ModulePackageValidator().validate_manifest(manifest(capabilities=[bad_capability]))

    assert "generic.example.echo_risk_level_allowed" in _failed_ids(checks)


def test_validator_catches_secret_like_metadata() -> None:
    valid = package_request()
    request = ModulePackageCreateRequest.model_construct(
        **{
            **valid.model_dump(mode="python"),
            "manifest": valid.manifest,
            "metadata": {"secret": "nope"},
        }
    )

    checks = ModulePackageValidator().validate_package(request)

    assert "package_metadata_safe" in _failed_ids(checks)


def test_validator_catches_shell_command_fields() -> None:
    bad_capability = dict(manifest().capabilities[0])
    bad_capability["shell_command"] = "echo unsafe"

    checks = ModulePackageValidator().validate_manifest(manifest(capabilities=[bad_capability]))

    assert "generic.example.echo_metadata_safe" in _failed_ids(checks)


def test_validator_catches_domain_specific_capability_name() -> None:
    bad_capability = dict(manifest().capabilities[0])
    bad_capability["capability_id"] = "generic.finance.report"

    checks = ModulePackageValidator().validate_manifest(manifest(capabilities=[bad_capability]))

    assert "generic.finance.report_capability_id_safe" in _failed_ids(checks)
