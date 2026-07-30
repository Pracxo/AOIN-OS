from __future__ import annotations

import os
import subprocess

from test_secure_runtime_integration_program_charter import REPO_ROOT


def run_script(relative: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["AION_SECURE_RUNTIME_INTEGRATION_SKIP_FULL_CHECK"] = "1"
    return subprocess.run(
        [str(REPO_ROOT / relative)],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


def test_secure_runtime_scripts_are_executable() -> None:
    for relative in (
        "scripts/secure-runtime-integration-program-authorization-check.sh",
        "scripts/secure-runtime-integration-program-no-go-regression.sh",
        "scripts/secure-runtime-integration-runtime-hold.sh",
    ):
        assert os.access(REPO_ROOT / relative, os.X_OK)


def test_secure_runtime_authorization_and_no_go_scripts_pass() -> None:
    for relative, expected in (
        (
            "scripts/secure-runtime-integration-program-authorization-check.sh",
            "secure runtime integration program authorization PASS",
        ),
        (
            "scripts/secure-runtime-integration-program-no-go-regression.sh",
            "secure runtime integration program no-go PASS",
        ),
    ):
        result = run_script(relative)
        assert result.returncode == 0, result.stdout + result.stderr
        assert expected in result.stdout


def test_secure_runtime_hold_defers_full_check_inside_pytest() -> None:
    result = run_script("scripts/secure-runtime-integration-runtime-hold.sh")

    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: full repository check deferred to outer gate" in result.stdout
    assert "secure runtime integration runtime hold PASS" in result.stdout
