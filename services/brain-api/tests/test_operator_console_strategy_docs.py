"""AION-087 operator console strategy documentation tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/operator-console/operator-console-strategy.md",
    "docs/operator-console/operator-console-workflows.md",
    "docs/operator-console/operator-view-spec.md",
    "docs/operator-console/operator-data-safety.md",
    "docs/operator-console/operator-action-boundaries.md",
    "docs/operator-console/operator-demo-map.md",
    "docs/operator-console/operator-console-no-go.md",
    "docs/operator-console/future-ui-milestones.md",
    "docs/adr/0078-operator-console-cli-api-first-decision.md",
]

EXAMPLES = [
    "examples/operator-console/operator-overview-flow.json",
    "examples/operator-console/release-readiness-flow.json",
    "examples/operator-console/module-lifecycle-flow.json",
    "examples/operator-console/provider-hardening-flow.json",
    "examples/operator-console/incident-review-flow.json",
    "examples/operator-console/golden-path-flow.json",
    "examples/operator-console/console-view-map.json",
]


def test_operator_console_strategy_docs_exist_and_are_indexed() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative

    adr_index = _text("docs/adr/README.md")
    assert "0078-operator-console-cli-api-first-decision.md" in adr_index


def test_operator_console_check_script_exists_is_executable_and_passes() -> None:
    script = ROOT / "scripts/operator-console-check.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR

    result = subprocess.run(
        [str(script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Operator console check PASS" in result.stdout


def test_operator_console_examples_are_valid_and_safe() -> None:
    for relative in EXAMPLES:
        payload = _json(relative)
        assert payload["external_calls_allowed"] is False
        serialized = json.dumps(payload, sort_keys=True).lower()
        assert "sk-" not in serialized
        assert "api_key" not in serialized
        assert "authorization" not in serialized

    view_map = _json("examples/operator-console/console-view-map.json")
    views = {item["view"] for item in view_map["views"]}
    assert "Module Lifecycle" in views
    assert {item["write_actions"] for item in view_map["views"]} <= {"dry_run", "forbidden"}

    provider_flow = _json("examples/operator-console/provider-hardening-flow.json")
    assert provider_flow["expected"]["external_call_ready"] is False

    module_flow = _json("examples/operator-console/module-lifecycle-flow.json")
    assert module_flow["expected"]["activation_allowed"] is False


def test_operator_console_docs_state_required_boundaries() -> None:
    combined = "\n".join(
        _text(relative)
        for relative in [
            *DOCS,
            "README.md",
            "AGENTS.md",
            "docs/architecture.md",
            "docs/cli.md",
            "docs/sdk.md",
        ]
    )

    for statement in [
        "CLI/API-first",
        "AION-087 adds no runtime UI",
        "no frontend dependencies",
        "raw prompts",
        "hidden reasoning",
        "secrets",
        "activate module",
        "external model calls",
    ]:
        assert statement.lower() in combined.lower()


def test_operator_console_does_not_change_runtime_surfaces() -> None:
    changed = _changed_files()
    assert not any(path.startswith("services/brain-api/src/aion_brain/api/") for path in changed)
    assert not any(
        path.startswith("packages/aion-sdk-python/aion_sdk/resources/") for path in changed
    )
    assert not any(
        path.startswith("packages/aion-sdk-python/aionctl/commands/") for path in changed
    )
    assert not any(Path(path).name in _FRONTEND_FILES for path in changed)


_FRONTEND_FILES = {
    "package.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "package-lock.json",
}


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _changed_files() -> list[str]:
    tracked = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [*tracked.stdout.splitlines(), *untracked.stdout.splitlines()]
