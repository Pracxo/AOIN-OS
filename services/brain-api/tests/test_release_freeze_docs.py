"""AION-080 final release freeze docs and script safety tests."""

from __future__ import annotations

import os
import re
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_version_and_release_documents_exist() -> None:
    assert _text("VERSION").strip() == "0.1.0"
    for relative in [
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "docs/release/v0.1-final-freeze.md",
        "docs/release/v0.1-final-evidence-summary.md",
        "docs/release/v0.1-tagging-guide.md",
        "docs/release/v0.1-release-baseline.md",
        "docs/release/v0.1-operator-acceptance.md",
        "docs/release/v0.1-known-limitations.md",
        "docs/adr/0072-v0.1-release-freeze-baseline.md",
    ]:
        assert (ROOT / relative).exists(), relative


def test_final_release_scripts_exist_and_are_executable() -> None:
    for relative in [
        "scripts/v0.1-final-verify.sh",
        "scripts/v0.1-freeze.sh",
        "scripts/v0.1-tag-preview.sh",
    ]:
        path = ROOT / relative
        assert path.exists()
        assert path.stat().st_mode & stat.S_IXUSR


def test_tag_preview_does_not_create_tag() -> None:
    before = _tags()
    result = subprocess.run(
        ["./scripts/v0.1-tag-preview.sh"],
        cwd=ROOT,
        check=False,
        text=True,
        capture_output=True,
    )
    after = _tags()
    assert result.returncode == 0, result.stdout + result.stderr
    assert before == after
    assert "git tag aion-v0.1.0" in result.stdout


def test_freeze_script_does_not_create_tag() -> None:
    text = _text("scripts/v0.1-freeze.sh")
    assert not re.search(r"^\s*git\s+tag\b", text, flags=re.MULTILINE)
    assert "git push" not in text


def test_final_verify_supports_offline_mode() -> None:
    text = _text("scripts/v0.1-final-verify.sh")
    assert "--offline-ok" in text
    assert "./scripts/rc-check.sh" in text
    assert "./scripts/final-docs-audit.sh" in text


def test_readme_links_final_release_docs() -> None:
    readme = _text("README.md")
    for link in [
        "docs/operations/operator-runbook.md",
        "docs/operations/local-demo-pack.md",
        "docs/operations/bootstrap.md",
        "docs/operations/golden-path.md",
        "docs/operations/release-candidate.md",
        "docs/operations/v0.1-release-handoff.md",
        "docs/release/v0.1-final-freeze.md",
        "docs/release/v0.1-no-go-conditions.md",
        "docs/release/v0.1-post-release-roadmap.md",
    ]:
        assert link in readme
    assert "production ready" not in readme.lower()
    assert "production-ready" not in readme.lower()


def test_release_docs_state_official_meaning_and_disabled_boundaries() -> None:
    text = _release_text()
    assert "AION means Adaptive Intelligence Orchestration Nexus" in text
    assert "AION OS means Adaptive Intelligence Orchestration Nexus Operating System" in text
    for boundary in [
        "No production auth",
        "No full autonomy",
        "No external model calls by default",
        "No external notification delivery by default",
        "No extension code loading",
        "No capability activation",
        "No hard delete",
        "No domain modules",
    ]:
        assert boundary.lower() in text.lower()


def test_release_docs_have_no_secret_or_private_reasoning_markers() -> None:
    text = _release_text().lower()
    for marker in [
        "sk-",
        "openai_api_key=",
        "password=",
        "bearer token",
        "private_key",
        "raw prompt",
        "raw_prompt",
        "hidden reasoning",
        "hidden_reasoning",
        "chain-of-thought",
        "chain_of_thought",
    ]:
        assert marker not in text


def test_release_scripts_do_not_publish_deploy_install_or_call_external_services() -> None:
    text = "\n".join(
        _text(relative)
        for relative in [
            "scripts/v0.1-final-verify.sh",
            "scripts/v0.1-freeze.sh",
            "scripts/v0.1-tag-preview.sh",
        ]
    ).lower()
    for forbidden in [
        "git push",
        "docker push",
        "kubectl",
        "terraform",
        "gh release",
        "npm publish",
        "twine upload",
        "pip install",
        "npm install",
        "brew install",
    ]:
        assert forbidden not in text
    assert "https://" not in text


def test_final_docs_audit_and_docs_check_pass() -> None:
    env = os.environ.copy()
    env["AION_BASE_URL"] = "http://127.0.0.1:9"
    for command in [["./scripts/docs-check.sh"], ["./scripts/final-docs-audit.sh"]]:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _tags() -> list[str]:
    result = subprocess.run(
        ["git", "tag", "--list", "aion-v0.1.0"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.splitlines()


def _release_text() -> str:
    paths = [
        "CHANGELOG.md",
        "RELEASE_NOTES.md",
        "docs/release/v0.1-final-freeze.md",
        "docs/release/v0.1-final-evidence-summary.md",
        "docs/release/v0.1-tagging-guide.md",
        "docs/release/v0.1-release-baseline.md",
        "docs/release/v0.1-operator-acceptance.md",
        "docs/release/v0.1-known-limitations.md",
        "docs/adr/0072-v0.1-release-freeze-baseline.md",
    ]
    return "\n".join(_text(path) for path in paths)
