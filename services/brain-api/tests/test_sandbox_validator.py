"""Sandbox validator tests."""

from aion_brain.contracts.sandbox import EgressRule, SandboxRunRequest
from aion_brain.sandbox.validator import SandboxValidator
from tests.sandbox_fakes import profile, settings


def test_sandbox_validator_fails_wildcard_egress() -> None:
    validator = SandboxValidator(settings())
    result = validator.validate_profile(
        profile(
            egress_rules=[
                EgressRule(
                    rule_id="wildcard",
                    destination_type="wildcard",
                    destination_ref="*",
                    ports=[443],
                    protocol="https",
                    action="allow",
                    metadata={"allow_wildcard": True},
                )
            ]
        )
    )

    assert result.status == "failed"
    assert "wildcard_egress_denied" in {check.check_id for check in result.checks}


def test_sandbox_validator_fails_docker_profile_execution_in_v01() -> None:
    validator = SandboxValidator(settings())
    docker_profile = profile(sandbox_type="docker")

    result = validator.validate_run(
        SandboxRunRequest(
            sandbox_profile_id=docker_profile.sandbox_profile_id,
            target_type="capability",
            target_id="test.echo",
        ),
        docker_profile,
    )

    assert result.status == "failed"
    assert "docker_firecracker_run_disabled" in {check.check_id for check in result.checks}
