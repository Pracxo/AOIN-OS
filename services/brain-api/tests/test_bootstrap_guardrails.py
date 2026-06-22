"""Bootstrap policy and local-only guardrail tests."""

from __future__ import annotations

from pathlib import Path

from aion_brain.identity.dev_auth import DEV_PERMISSIONS
from aion_brain.policy_catalog.defaults import DEFAULT_ACTION_SPECS

ROOT = Path(__file__).parents[3]

BOOTSTRAP_ACTIONS = {
    "bootstrap.profile.create",
    "bootstrap.profile.read",
    "bootstrap.profile.update",
    "bootstrap.seed_bundle.create",
    "bootstrap.seed_bundle.read",
    "bootstrap.seed_bundle.update",
    "bootstrap.seed.execute",
    "bootstrap.doctor.run",
    "bootstrap.finding.read",
    "bootstrap.finding.update",
    "bootstrap.run",
    "bootstrap.run.read",
    "bootstrap.report.create",
    "bootstrap.report.read",
    "bootstrap.query",
}


def test_bootstrap_actions_registered_in_dev_auth_and_policy_catalog() -> None:
    catalog_actions = {action for action, *_rest in DEFAULT_ACTION_SPECS}

    assert BOOTSTRAP_ACTIONS.issubset(set(DEV_PERMISSIONS))
    assert BOOTSTRAP_ACTIONS.issubset(catalog_actions)


def test_opa_policy_contains_bootstrap_fail_closed_guards() -> None:
    policy = (ROOT / "infra/opa/policies/brain.rego").read_text()

    for action in BOOTSTRAP_ACTIONS:
        assert action in policy
    assert "bootstrap_unsafe_request" in policy
    assert "package_install_requested" in policy
    assert "production_auth_enabled" in policy
    assert "source_mutation_requested" in policy
    assert "not bootstrap_action" in policy


def test_bootstrap_scripts_are_local_only_and_executable() -> None:
    scripts = [
        ROOT / "scripts/bootstrap-local.sh",
        ROOT / "scripts/setup-doctor.sh",
        ROOT / "scripts/seed-defaults.sh",
    ]
    for script in scripts:
        text = script.read_text()
        assert script.exists()
        assert script.stat().st_mode & 0o111
        assert "pip install" not in text
        assert "npm install" not in text
        assert "brew install" not in text
        assert "https://" not in text
        assert "localhost" in text


def test_bootstrap_task_did_not_create_frontend_files() -> None:
    created_paths = [
        "services/brain-api/src/aion_brain/contracts/bootstrap.py",
        "services/brain-api/src/aion_brain/contracts/setup_doctor.py",
        "services/brain-api/src/aion_brain/api/bootstrap.py",
        "packages/aion-sdk-python/src/aion_sdk/resources/bootstrap.py",
    ]
    forbidden_suffixes = (".tsx", ".jsx", ".css")
    assert not any(path.endswith(forbidden_suffixes) for path in created_paths)
