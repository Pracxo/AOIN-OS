"""Repository quality control tests."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_repo_health_script_exists() -> None:
    script = ROOT / "scripts" / "repo-health.sh"

    assert script.exists()
    assert script.stat().st_mode & 0o111


def test_release_candidate_script_exists() -> None:
    script = ROOT / "scripts" / "release-candidate-check.sh"

    assert script.exists()
    assert script.stat().st_mode & 0o111


def test_no_domain_drift_script_exists() -> None:
    script = ROOT / "scripts" / "verify-no-domain-drift.sh"

    assert script.exists()
    assert script.stat().st_mode & 0o111


def test_github_workflows_exist() -> None:
    workflows = ROOT / ".github" / "workflows"

    assert (workflows / "ci.yml").exists()
    assert (workflows / "docker.yml").exists()
    assert (workflows / "contracts.yml").exists()
    assert (workflows / "policy.yml").exists()
    assert (workflows / "sdk.yml").exists()


def test_operations_docs_exist() -> None:
    operations = ROOT / "docs" / "operations"

    assert (operations / "local-ops-runbook.md").exists()
    assert (operations / "quality-gates.md").exists()
    assert (operations / "release-candidate-checklist.md").exists()
    assert (ROOT / "docs" / "adr" / "README.md").exists()
