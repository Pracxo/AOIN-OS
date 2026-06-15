"""Module certifier sandbox integration tests."""

from aion_brain.config import Settings
from aion_brain.module_developer.certifier import ModuleCertifier


def test_module_certifier_includes_sandbox_checks() -> None:
    certifier = ModuleCertifier(
        repository=object(),
        validator=object(),
        capability_service=object(),
        runtime_gateway=object(),
        policy_adapter=object(),
        autonomy_governor=object(),
        risk_engine=object(),
        telemetry_service=None,
        settings=Settings(_env_file=None),
    )

    checks = certifier._sandbox_checks(  # noqa: SLF001
        {
            "capability_id": "test.echo",
            "execution_mode": "async",
            "metadata": {"sandbox_profile_id": "sandbox-profile-1"},
            "secret_refs": [],
            "connector_refs": [],
            "runtime_permissions": ["runtime.execute"],
            "egress_rules": [],
            "process_spawn_enabled": False,
            "filesystem_write_enabled": False,
        }
    )

    check_ids = {check.check_id for check in checks}
    assert "test.echo_sandbox_profile_declared" in check_ids
    assert "test.echo_no_wildcard_egress" in check_ids
    assert "test.echo_process_spawn_disabled" in check_ids
