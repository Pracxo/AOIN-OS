"""Sandbox contract tests."""

import pytest
from pydantic import ValidationError

from aion_brain.contracts.sandbox import (
    EgressRule,
    FilesystemRule,
    ResourceLimits,
    RuntimePermissionGrant,
    SandboxProfile,
)
from tests.sandbox_fakes import profile, resource_limits, runtime_permission


def test_resource_limits_validate_bounds() -> None:
    ResourceLimits(
        cpu_millis=100,
        memory_mb=64,
        timeout_seconds=1,
        max_output_bytes=1024,
        max_files=0,
        max_file_bytes=0,
    )

    with pytest.raises(ValidationError):
        resource_limits(cpu_millis=99)


def test_egress_rule_rejects_wildcard_unless_explicitly_allowed() -> None:
    with pytest.raises(ValidationError):
        EgressRule(
            rule_id="wildcard",
            destination_type="wildcard",
            destination_ref="*",
            ports=[443],
            protocol="https",
            action="allow",
        )

    rule = EgressRule(
        rule_id="wildcard",
        destination_type="wildcard",
        destination_ref="*",
        ports=[443],
        protocol="https",
        action="allow",
        metadata={"allow_wildcard": True},
    )
    assert rule.destination_type == "wildcard"


def test_filesystem_rule_rejects_path_traversal_and_docker_socket() -> None:
    with pytest.raises(ValidationError):
        FilesystemRule(rule_id="escape", path_ref="../host", access="read", action="allow")

    with pytest.raises(ValidationError):
        FilesystemRule(
            rule_id="socket",
            path_ref="/var/run/docker.sock",
            access="read",
            action="allow",
        )


def test_sandbox_profile_validates_type_and_rejects_process_spawn() -> None:
    payload = profile().model_dump(mode="python")
    payload["sandbox_type"] = "unknown"
    with pytest.raises(ValidationError):
        SandboxProfile(**payload)

    with pytest.raises(ValidationError):
        profile(process_spawn_enabled=True)


def test_runtime_permission_grant_validates_target_type() -> None:
    with pytest.raises(ValidationError):
        RuntimePermissionGrant(
            runtime_permission_id="grant-1",
            target_type="unknown",
            target_id="target-1",
            sandbox_profile_id=None,
            owner_scope=["workspace:main"],
            permissions=[runtime_permission()],
            secret_refs=[],
            connector_refs=[],
            status="active",
        )
