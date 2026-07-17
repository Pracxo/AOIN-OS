"""AION-103 static console UX refinement regression tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = ROOT / "operator-console-static"
EXAMPLE_DIR = ROOT / "examples" / "operator-console"


def test_static_console_ux_script_exists_and_passes() -> None:
    script = ROOT / "scripts/static-console-ux-check.sh"
    assert script.exists()
    assert os.access(script, os.X_OK)
    assert script.stat().st_mode & stat.S_IXUSR

    result = subprocess.run(
        [str(script)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Static console UX check PASS" in result.stdout


def test_static_console_ux_docs_and_adr_exist() -> None:
    for relative in [
        "docs/operator-console/static-console-ux-refinement.md",
        "docs/operator-console/static-console-accessibility-checklist.md",
        "docs/operator-console/static-console-navigation-model.md",
        "docs/operator-console/static-console-information-architecture.md",
        "docs/adr/0094-static-console-ux-refinement.md",
    ]:
        assert (ROOT / relative).exists(), relative
    assert "0094-static-console-ux-refinement.md" in _text(ROOT / "docs/adr/README.md")


def test_navigation_map_and_accessibility_result_are_valid() -> None:
    nav = _json(EXAMPLE_DIR / "static-console-navigation-map.json")
    assert nav["status"] == "passed"
    groups = {group["name"] for group in nav["groups"]}
    for required in [
        "Platform",
        "Modules",
        "Providers",
        "Actions",
        "Auth and Sessions",
        "Evidence",
        "Safety",
    ]:
        assert required in groups

    allowed_commands = {
        "./scripts/ui-release-gate.sh",
        "./scripts/static-console-safety-check.sh",
        "./scripts/operator-platform-regression.sh",
        "./scripts/operator-platform-freeze-gate.sh",
        "./scripts/connector-platform-regression.sh",
        "./scripts/connector-platform-stabilization-gate.sh",
        "./scripts/platform-integration-checkpoint.sh",
        "./scripts/platform-integration-freeze-check.sh",
        "./scripts/platform-integration-no-go-regression.sh",
        "./scripts/post-v01-release-candidate-gate.sh",
        "./scripts/post-v01-release-candidate-freeze.sh",
        "./scripts/post-v01-release-candidate-no-go-regression.sh",
        "./scripts/v02-planning-charter-check.sh",
        "./scripts/v02-planning-no-go-regression.sh",
        "./scripts/v02-planning-stabilization-gate.sh",
        "./scripts/v02-planning-freeze-check.sh",
        "./scripts/v02-planning-stabilization-no-go-regression.sh",
        "./scripts/v02-readiness-final-review.sh",
        "./scripts/v02-readiness-final-freeze.sh",
        "./scripts/v02-readiness-final-no-go-regression.sh",
        "./scripts/v02-implementation-kickoff-boundary-check.sh",
        "./scripts/v02-implementation-kickoff-freeze.sh",
        "./scripts/v02-implementation-kickoff-no-go-regression.sh",
        "./scripts/v02-approval-workflow-stabilization-gate.sh",
        "./scripts/v02-approval-workflow-freeze.sh",
        "./scripts/v02-approval-workflow-no-go-regression.sh",
        "./scripts/v02-workstream-intake-readiness-gate.sh",
        "./scripts/v02-workstream-intake-freeze.sh",
        "./scripts/v02-workstream-intake-no-go-regression.sh",
        "./scripts/v02-preimplementation-master-freeze.sh",
        "./scripts/v02-preimplementation-final-baseline-check.sh",
        "./scripts/v02-preimplementation-master-no-go-regression.sh",
        "./scripts/v02-workstream-proposal-registry-check.sh",
        "./scripts/v02-proposal-registry-freeze.sh",
        "./scripts/v02-proposal-registry-no-go-regression.sh",
        "./scripts/v02-proposal-registry-stabilization-gate.sh",
        "./scripts/v02-approval-queue-freeze.sh",
        "./scripts/v02-approval-queue-no-go-regression.sh",
        "./scripts/v02-planning-master-checkpoint.sh",
        "./scripts/v02-planning-master-freeze.sh",
        "./scripts/v02-planning-master-no-go-regression.sh",
        "./scripts/v02-final-planning-release-gate.sh",
        "./scripts/v02-final-planning-freeze.sh",
        "./scripts/v02-final-planning-no-go-regression.sh",
        "./scripts/v02-planning-track-closeout.sh",
        "./scripts/v02-planning-track-handoff-freeze.sh",
        "./scripts/v02-planning-track-closeout-no-go-regression.sh",
        "./scripts/v02-implementation-request-pack-check.sh",
        "./scripts/v02-request-pack-freeze.sh",
        "./scripts/v02-request-pack-no-go-regression.sh",
        "./scripts/v02-request-pack-stabilization-gate.sh",
        "./scripts/v02-request-pack-submission-freeze.sh",
        "./scripts/v02-request-pack-stabilization-no-go-regression.sh",
        "./scripts/v02-request-pack-final-review.sh",
        "./scripts/v02-preapproval-submission-freeze.sh",
        "./scripts/v02-request-pack-final-no-go-regression.sh",
        "./scripts/v02-submission-registry-preview-check.sh",
        "./scripts/v02-preapproval-queue-freeze.sh",
        "./scripts/v02-preapproval-queue-no-go-regression.sh",
        "./scripts/v02-submission-registry-stabilization-gate.sh",
        "./scripts/v02-submission-registry-freeze.sh",
        "./scripts/v02-submission-registry-stabilization-no-go-regression.sh",
        "./scripts/v02-preapproval-review-board-check.sh",
        "./scripts/v02-review-board-freeze.sh",
        "./scripts/v02-review-board-no-go-regression.sh",
        "./scripts/v02-review-board-stabilization-gate.sh",
        "./scripts/v02-review-routing-freeze.sh",
        "./scripts/v02-review-board-stabilization-no-go-regression.sh",
        "./scripts/v02-decision-package-preview-check.sh",
        "./scripts/v02-decision-package-freeze.sh",
        "./scripts/v02-decision-package-no-go-regression.sh",
        "./scripts/v02-decision-package-stabilization-gate.sh",
        "./scripts/v02-approval-readiness-freeze.sh",
        "./scripts/v02-decision-package-stabilization-no-go-regression.sh",
        "./scripts/v02-decision-package-final-review.sh",
        "./scripts/v02-runtime-decision-lock-freeze.sh",
        "./scripts/v02-decision-package-final-no-go-regression.sh",
        "./scripts/v02-approval-docket-preview-check.sh",
        "./scripts/v02-runtime-approval-review-freeze.sh",
        "./scripts/v02-approval-docket-no-go-regression.sh",
        "./scripts/v02-approval-docket-stabilization-gate.sh",
        "./scripts/v02-implementation-decision-record-freeze.sh",
        "./scripts/v02-approval-docket-stabilization-no-go-regression.sh",
        "./scripts/v02-approval-docket-final-review.sh",
        "./scripts/v02-runtime-approval-lock-freeze.sh",
        "./scripts/v02-approval-docket-final-no-go-regression.sh",
        "./scripts/v02-runtime-approval-board-preview-check.sh",
        "./scripts/v02-approval-vote-record-freeze.sh",
        "./scripts/v02-runtime-approval-board-no-go-regression.sh",
        "./scripts/v02-runtime-approval-board-stabilization-gate.sh",
        "./scripts/v02-approval-vote-record-stabilization-freeze.sh",
        "./scripts/v02-runtime-approval-board-stabilization-no-go-regression.sh",
        "./scripts/v02-runtime-approval-board-final-review.sh",
        "./scripts/v02-implementation-go-no-go-final-freeze.sh",
        "./scripts/v02-runtime-approval-board-final-no-go-regression.sh",
        "./scripts/v02-implementation-authorization-preview-check.sh",
        "./scripts/v02-runtime-enablement-guard-freeze.sh",
        "./scripts/v02-implementation-authorization-no-go-regression.sh",
        "./scripts/v02-explicit-approval-record-freeze.sh",
        "./scripts/v02-implementation-authorization-stabilization-no-go-regression.sh",
        "./scripts/v02-implementation-authorization-stabilization-gate.sh",
        "./scripts/v02-implementation-authorization-final-review.sh",
        "./scripts/v02-runtime-enablement-guard-final-freeze.sh",
        "./scripts/v02-implementation-authorization-final-no-go-regression.sh",
        "./scripts/v02-authorization-track-closeout.sh",
        "./scripts/v02-runtime-enablement-master-lock-freeze.sh",
        "./scripts/v02-authorization-track-closeout-no-go-regression.sh",
        "./scripts/v02-production-auth-authorization-check.sh",
        "./scripts/v02-production-auth-runtime-guard-hold.sh",
        "./scripts/v02-production-auth-authorization-no-go-regression.sh",
        "./scripts/v02-production-auth-stabilization-authorization-check.sh",
        "./scripts/v02-production-auth-stabilization-runtime-guard-hold.sh",
        "./scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh",
        "./scripts/production-auth-core-stabilization-no-go-regression.sh",
        "./scripts/production-auth-core-stabilization-check.sh",
        "./scripts/production-auth-core-stabilization-runtime-hold.sh",
        "./scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh",
        "./scripts/v02-production-auth-request-boundary-authorization-check.sh",
        "./scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
        "./scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
        "./scripts/production-auth-request-identity-stabilization-no-go-regression.sh",
        "./scripts/production-auth-request-identity-stabilization-check.sh",
        "./scripts/production-auth-request-identity-stabilization-runtime-hold.sh",
        "./scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh",
        "./scripts/v02-actor-context-trust-boundary-authorization-check.sh",
        "./scripts/docs-check.sh",
    }
    assert set(nav["safe_copy_commands"]) == allowed_commands
    assert all(value is False for value in nav["forbidden_surface"].values())

    accessibility = _json(EXAMPLE_DIR / "static-console-accessibility-check-result.json")
    assert accessibility["expected_status"] == "passed"
    assert all(item["expected_status"] == "passed" for item in accessibility["checks"])
    assert accessibility["write_actions_present"] is False
    assert accessibility["external_calls_present"] is False


def test_static_console_has_navigation_accessibility_and_safe_command_copy() -> None:
    html = _text(STATIC_DIR / "index.html")
    lowered = html.lower()
    assert 'class="skip-link"' in html
    assert 'id="console-main"' in html
    for banner in [
        "read-only",
        "no activation",
        "no execution",
        "no provider calls",
        "no login",
        "no credentials",
    ]:
        assert banner in lowered
    for group in [
        "Platform",
        "Modules",
        "Providers",
        "Actions",
        "Auth and Sessions",
        "Evidence",
        "Safety",
    ]:
        assert group in html
    assert "<form" not in lowered
    assert "<input" not in lowered

    commands = set(_data_commands(html))
    assert commands == {
        "./scripts/ui-release-gate.sh",
        "./scripts/static-console-safety-check.sh",
        "./scripts/operator-platform-regression.sh",
        "./scripts/operator-platform-freeze-gate.sh",
        "./scripts/connector-platform-regression.sh",
        "./scripts/connector-platform-stabilization-gate.sh",
        "./scripts/platform-integration-checkpoint.sh",
        "./scripts/platform-integration-freeze-check.sh",
        "./scripts/platform-integration-no-go-regression.sh",
        "./scripts/post-v01-release-candidate-gate.sh",
        "./scripts/post-v01-release-candidate-freeze.sh",
        "./scripts/post-v01-release-candidate-no-go-regression.sh",
        "./scripts/v02-planning-charter-check.sh",
        "./scripts/v02-planning-no-go-regression.sh",
        "./scripts/v02-planning-stabilization-gate.sh",
        "./scripts/v02-planning-freeze-check.sh",
        "./scripts/v02-planning-stabilization-no-go-regression.sh",
        "./scripts/v02-readiness-final-review.sh",
        "./scripts/v02-readiness-final-freeze.sh",
        "./scripts/v02-readiness-final-no-go-regression.sh",
        "./scripts/v02-implementation-kickoff-boundary-check.sh",
        "./scripts/v02-implementation-kickoff-freeze.sh",
        "./scripts/v02-implementation-kickoff-no-go-regression.sh",
        "./scripts/v02-approval-workflow-stabilization-gate.sh",
        "./scripts/v02-approval-workflow-freeze.sh",
        "./scripts/v02-approval-workflow-no-go-regression.sh",
        "./scripts/v02-workstream-intake-readiness-gate.sh",
        "./scripts/v02-workstream-intake-freeze.sh",
        "./scripts/v02-workstream-intake-no-go-regression.sh",
        "./scripts/v02-preimplementation-master-freeze.sh",
        "./scripts/v02-preimplementation-final-baseline-check.sh",
        "./scripts/v02-preimplementation-master-no-go-regression.sh",
        "./scripts/v02-workstream-proposal-registry-check.sh",
        "./scripts/v02-proposal-registry-freeze.sh",
        "./scripts/v02-proposal-registry-no-go-regression.sh",
        "./scripts/v02-proposal-registry-stabilization-gate.sh",
        "./scripts/v02-approval-queue-freeze.sh",
        "./scripts/v02-approval-queue-no-go-regression.sh",
        "./scripts/v02-planning-master-checkpoint.sh",
        "./scripts/v02-planning-master-freeze.sh",
        "./scripts/v02-planning-master-no-go-regression.sh",
        "./scripts/v02-final-planning-release-gate.sh",
        "./scripts/v02-final-planning-freeze.sh",
        "./scripts/v02-final-planning-no-go-regression.sh",
        "./scripts/v02-planning-track-closeout.sh",
        "./scripts/v02-planning-track-handoff-freeze.sh",
        "./scripts/v02-planning-track-closeout-no-go-regression.sh",
        "./scripts/v02-implementation-request-pack-check.sh",
        "./scripts/v02-request-pack-freeze.sh",
        "./scripts/v02-request-pack-no-go-regression.sh",
        "./scripts/v02-request-pack-stabilization-gate.sh",
        "./scripts/v02-request-pack-submission-freeze.sh",
        "./scripts/v02-request-pack-stabilization-no-go-regression.sh",
        "./scripts/v02-request-pack-final-review.sh",
        "./scripts/v02-preapproval-submission-freeze.sh",
        "./scripts/v02-request-pack-final-no-go-regression.sh",
        "./scripts/v02-submission-registry-preview-check.sh",
        "./scripts/v02-preapproval-queue-freeze.sh",
        "./scripts/v02-preapproval-queue-no-go-regression.sh",
        "./scripts/v02-submission-registry-stabilization-gate.sh",
        "./scripts/v02-submission-registry-freeze.sh",
        "./scripts/v02-submission-registry-stabilization-no-go-regression.sh",
        "./scripts/v02-preapproval-review-board-check.sh",
        "./scripts/v02-review-board-freeze.sh",
        "./scripts/v02-review-board-no-go-regression.sh",
        "./scripts/v02-review-board-stabilization-gate.sh",
        "./scripts/v02-review-routing-freeze.sh",
        "./scripts/v02-review-board-stabilization-no-go-regression.sh",
        "./scripts/v02-decision-package-preview-check.sh",
        "./scripts/v02-decision-package-freeze.sh",
        "./scripts/v02-decision-package-no-go-regression.sh",
        "./scripts/v02-decision-package-stabilization-gate.sh",
        "./scripts/v02-approval-readiness-freeze.sh",
        "./scripts/v02-decision-package-stabilization-no-go-regression.sh",
        "./scripts/v02-decision-package-final-review.sh",
        "./scripts/v02-runtime-decision-lock-freeze.sh",
        "./scripts/v02-decision-package-final-no-go-regression.sh",
        "./scripts/v02-approval-docket-preview-check.sh",
        "./scripts/v02-runtime-approval-review-freeze.sh",
        "./scripts/v02-approval-docket-no-go-regression.sh",
        "./scripts/v02-approval-docket-stabilization-gate.sh",
        "./scripts/v02-implementation-decision-record-freeze.sh",
        "./scripts/v02-approval-docket-stabilization-no-go-regression.sh",
        "./scripts/v02-approval-docket-final-review.sh",
        "./scripts/v02-runtime-approval-lock-freeze.sh",
        "./scripts/v02-approval-docket-final-no-go-regression.sh",
        "./scripts/v02-runtime-approval-board-preview-check.sh",
        "./scripts/v02-approval-vote-record-freeze.sh",
        "./scripts/v02-runtime-approval-board-no-go-regression.sh",
        "./scripts/v02-runtime-approval-board-stabilization-gate.sh",
        "./scripts/v02-approval-vote-record-stabilization-freeze.sh",
        "./scripts/v02-runtime-approval-board-stabilization-no-go-regression.sh",
        "./scripts/v02-runtime-approval-board-final-review.sh",
        "./scripts/v02-implementation-go-no-go-final-freeze.sh",
        "./scripts/v02-runtime-approval-board-final-no-go-regression.sh",
        "./scripts/v02-implementation-authorization-preview-check.sh",
        "./scripts/v02-runtime-enablement-guard-freeze.sh",
        "./scripts/v02-implementation-authorization-no-go-regression.sh",
        "./scripts/v02-implementation-authorization-stabilization-gate.sh",
        "./scripts/v02-implementation-authorization-stabilization-no-go-regression.sh",
        "./scripts/v02-explicit-approval-record-freeze.sh",
        "./scripts/v02-implementation-authorization-final-review.sh",
        "./scripts/v02-runtime-enablement-guard-final-freeze.sh",
        "./scripts/v02-implementation-authorization-final-no-go-regression.sh",
        "./scripts/v02-authorization-track-closeout.sh",
        "./scripts/v02-runtime-enablement-master-lock-freeze.sh",
        "./scripts/v02-authorization-track-closeout-no-go-regression.sh",
        "./scripts/v02-production-auth-authorization-check.sh",
        "./scripts/v02-production-auth-runtime-guard-hold.sh",
        "./scripts/v02-production-auth-authorization-no-go-regression.sh",
        "./scripts/v02-production-auth-stabilization-authorization-check.sh",
        "./scripts/v02-production-auth-stabilization-runtime-guard-hold.sh",
        "./scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh",
        "./scripts/production-auth-core-stabilization-no-go-regression.sh",
        "./scripts/production-auth-core-stabilization-check.sh",
            "./scripts/production-auth-core-stabilization-runtime-hold.sh",
            "./scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh",
            "./scripts/v02-production-auth-request-boundary-authorization-check.sh",
            "./scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
            "./scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
            "./scripts/production-auth-request-identity-stabilization-no-go-regression.sh",
            "./scripts/production-auth-request-identity-stabilization-check.sh",
            "./scripts/production-auth-request-identity-stabilization-runtime-hold.sh",
            "./scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh",
            "./scripts/v02-actor-context-trust-boundary-authorization-check.sh",
            "./scripts/docs-check.sh",
        }


def test_static_console_js_and_css_keep_static_boundaries() -> None:
    app = _text(STATIC_DIR / "app.js")
    css = _text(STATIC_DIR / "styles.css").lower()
    assert "SAFE_COPY_COMMANDS" in app
    assert "setActiveGroup" in app
    assert "renderSafetyBlockerView" in app
    assert "isLocalApiOrigin" in app
    assert 'parsed.hostname === "localhost"' in app
    assert 'parsed.hostname === "127.0.0.1"' in app
    assert 'method: "PUT"' not in app
    assert 'method: "PATCH"' not in app
    assert 'method: "DELETE"' not in app
    assert "localStorage" not in app
    assert "sessionStorage" not in app
    assert ":focus-visible" in css
    assert "@import" not in css
    assert "url(http" not in css


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _text(path: Path) -> str:
    return path.read_text()


def _data_commands(html: str) -> list[str]:
    prefix = 'data-command="'
    commands: list[str] = []
    for chunk in html.split(prefix)[1:]:
        commands.append(chunk.split('"', 1)[0])
    return commands
