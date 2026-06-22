"""AION-079 release handoff docs and demo pack tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_release_handoff_scripts_exist_and_are_executable() -> None:
    for relative in [
        "scripts/demo-local.sh",
        "scripts/operator-runbook-check.sh",
        "scripts/docs-check.sh",
        "scripts/final-docs-audit.sh",
    ]:
        path = ROOT / relative
        assert path.exists()
        assert path.stat().st_mode & stat.S_IXUSR


def test_demo_json_examples_are_valid_and_safe() -> None:
    manifest = _json("examples/demo/generic-extension-manifest.json")
    assert manifest["package_type"] == "module"
    assert manifest["declared_dependencies"] == []
    assert manifest["declared_routes"] == []
    assert manifest["metadata"]["remote_sources_allowed"] is False
    assert manifest["metadata"]["activation_allowed"] is False
    assert manifest["metadata"]["route_registration_allowed"] is False
    assert manifest["metadata"]["payloads_included"] is False
    assert manifest["metadata"]["code_loading_allowed"] is False
    _assert_no_key(manifest, {"binary", "entrypoint", "package_bytes", "source_code"})

    for relative in [
        "examples/demo/golden-path-request.json",
        "examples/demo/rc-gate-request.json",
        "examples/demo/bootstrap-run-request.json",
    ]:
        assert isinstance(_json(relative), dict)


def test_release_handoff_docs_include_required_operator_content() -> None:
    runbook = _text("docs/operations/operator-runbook.md")
    assert "AION = Adaptive Intelligence Orchestration Nexus" in runbook
    assert "AION OS = Adaptive Intelligence Orchestration Nexus Operating System" in runbook
    for boundary in [
        "does not enable production auth",
        "does not enable full autonomy",
        "does not execute model-generated tool calls",
        "does not load extension code",
        "does not activate capability bindings",
        "does not send external notifications",
        "does not hard-delete records",
    ]:
        assert boundary in runbook


def test_release_handoff_docs_include_required_checks_and_no_go_conditions() -> None:
    troubleshooting = _text("docs/operations/troubleshooting.md")
    local_demo = _text("docs/operations/local-demo-pack.md")
    no_go = _text("docs/release/v0.1-no-go-conditions.md")

    assert "OPA policy unknown action" in troubleshooting
    assert "docker compose config --quiet" in local_demo
    assert "curl -fsS http://localhost:8080/health" in local_demo
    assert "external model calls enabled by default" in no_go
    assert "extension code loading enabled" in no_go


def test_release_handoff_audit_scripts_pass() -> None:
    env = os.environ.copy()
    env["AION_BASE_URL"] = "http://127.0.0.1:9"
    for command in [
        ["./scripts/docs-check.sh"],
        ["./scripts/final-docs-audit.sh"],
    ]:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            check=False,
            text=True,
            capture_output=True,
        )
        assert result.returncode == 0, result.stdout + result.stderr


def test_release_handoff_docs_and_examples_have_no_blocking_markers() -> None:
    paths = [
        ROOT / "docs/operations/operator-runbook.md",
        ROOT / "docs/operations/local-demo-pack.md",
        ROOT / "docs/operations/troubleshooting.md",
        ROOT / "docs/operations/v0.1-release-handoff.md",
        ROOT / "docs/release/v0.1-release-candidate-checklist.md",
        ROOT / "docs/release/v0.1-demo-script.md",
        ROOT / "docs/release/v0.1-no-go-conditions.md",
        ROOT / "docs/release/v0.1-post-release-roadmap.md",
        *sorted((ROOT / "examples/demo").glob("*")),
    ]
    forbidden = [
        "sk-",
        "OPENAI_API_KEY=",
        "password=",
        "bearer token",
        "private_key",
        "raw prompt",
        "raw_prompt",
        "hidden reasoning",
        "hidden_reasoning",
        "chain-of-thought",
        "chain_of_thought",
    ]
    for path in paths:
        if path.is_file():
            text = path.read_text().lower()
            assert "TODO_RELEASE_BLOCKER".lower() not in text
            for marker in forbidden:
                assert marker.lower() not in text, f"{marker} in {path}"


def test_demo_examples_contain_no_vertical_logic_terms() -> None:
    text = "\n".join(path.read_text().lower() for path in (ROOT / "examples/demo").glob("*"))
    for term in ["finance", "trading", "medical", "healthcare", "legal", "procurement"]:
        assert term not in text


def _json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _assert_no_key(value: object, banned: set[str]) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            assert str(key).lower() not in banned
            _assert_no_key(nested, banned)
    elif isinstance(value, list):
        for item in value:
            _assert_no_key(item, banned)
