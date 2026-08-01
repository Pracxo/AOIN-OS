from __future__ import annotations

import json
import subprocess
from pathlib import Path

from aion_brain.contracts import v02_release_qualification as c

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts/v02-release-qualification-local-run.py"
PYTHON = REPO_ROOT / "services/brain-api/.venv/bin/python"


def test_uninstalled_runner_requires_secure_paths_and_writes_redacted_output(tmp_path):
    fixture_names = {
        "candidate": "candidate.json",
        "gap-matrix": "gap-matrix.json",
        "auth-composition": "auth-composition.json",
        "request-identity": "request-identity.json",
        "replay-plan": "replay-plan.json",
        "identity-providers": "identity-providers.json",
        "key-policies": "key-policies.json",
        "protected-material": "protected-material.json",
        "credential-policies": "credential-policies.json",
        "token-policies": "token-policies.json",
        "session-policies": "session-policies.json",
        "artifact-manifests": "artifact-manifests.json",
        "rollback-plans": "rollback-plans.json",
        "observability": "observability.json",
        "threat-model": "threat-model.json",
        "release-gates": "release-gates.json",
        "staging-plan": "staging-plan.json",
    }
    for label, filename in fixture_names.items():
        path = tmp_path / filename
        path.write_text(json.dumps({"fixture_id": label}), encoding="utf-8")
        path.chmod(0o600)

    temp_root = tmp_path / "secure-root"
    temp_root.mkdir(mode=0o700)
    output = tmp_path / "result.json"
    command = [
        str(PYTHON),
        str(RUNNER),
        "run-pilot",
        "--authorization",
        c.AUTHORIZATION_TRANSACTION_ID,
        "--temporary-root",
        str(temp_root),
        "--output",
        str(output),
        "--confirm",
        c.LOCAL_QUALIFICATION_CONFIRMATION_TEXT,
    ]
    for label, filename in fixture_names.items():
        command.extend([f"--{label}", str(tmp_path / filename)])

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["pilot_id"] == c.PILOT_ID
    assert payload["runner_installed"] is False
    assert payload["temporary_paths_retained"] == 0
    assert payload["v02_release_ready"] is False
    assert sum(payload["prohibited_effect_counters"].values()) == 0


def test_runner_rejects_broad_fixture_permissions(tmp_path):
    fixture = tmp_path / "fixture.json"
    fixture.write_text("{}", encoding="utf-8")
    fixture.chmod(0o644)
    temp_root = tmp_path / "secure-root"
    temp_root.mkdir(mode=0o700)
    output = tmp_path / "result.json"
    command = [
        str(PYTHON),
        str(RUNNER),
        "run-pilot",
        "--authorization",
        c.AUTHORIZATION_TRANSACTION_ID,
        "--candidate",
        str(fixture),
        "--gap-matrix",
        str(fixture),
        "--auth-composition",
        str(fixture),
        "--request-identity",
        str(fixture),
        "--replay-plan",
        str(fixture),
        "--identity-providers",
        str(fixture),
        "--key-policies",
        str(fixture),
        "--protected-material",
        str(fixture),
        "--credential-policies",
        str(fixture),
        "--token-policies",
        str(fixture),
        "--session-policies",
        str(fixture),
        "--artifact-manifests",
        str(fixture),
        "--rollback-plans",
        str(fixture),
        "--observability",
        str(fixture),
        "--threat-model",
        str(fixture),
        "--release-gates",
        str(fixture),
        "--staging-plan",
        str(fixture),
        "--temporary-root",
        str(temp_root),
        "--output",
        str(output),
        "--confirm",
        c.LOCAL_QUALIFICATION_CONFIRMATION_TEXT,
    ]

    completed = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "permissions" in completed.stderr
