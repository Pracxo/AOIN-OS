from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_auth_design_docs_exist() -> None:
    for path in [
        "docs/auth/local-auth-design.md",
        "docs/auth/operator-identity-model.md",
        "docs/auth/operator-session-boundary.md",
        "docs/auth/operator-role-model.md",
        "docs/auth/operator-access-matrix.md",
        "docs/auth/operator-auth-threat-model.md",
        "docs/auth/production-auth-prerequisites.md",
        "docs/auth/auth-no-go-conditions.md",
        "docs/auth/future-auth-implementation-plan.md",
    ]:
        assert (ROOT / path).is_file()


def test_auth_design_docs_state_boundaries() -> None:
    text = (ROOT / "docs/auth/local-auth-design.md").read_text()
    assert "no production auth is implemented" in text
    assert "No credentials are stored" in text
    assert "No external identity provider is integrated" in text
    assert "No login endpoint is added" in text
    assert "ActorContext remains the current internal context mechanism" in text
    assert "Policy remains authoritative" in text


def test_auth_adr_is_indexed() -> None:
    assert (ROOT / "docs/adr/0084-local-auth-design-for-operator-console.md").is_file()
    index = (ROOT / "docs/adr/README.md").read_text()
    assert "0084-local-auth-design-for-operator-console.md" in index


def test_auth_examples_are_valid_and_redacted() -> None:
    blocked = (
        "token",
        "password",
        "secret",
        "api_key",
        "private_key",
        "authorization",
        "bearer",
    )
    aion_104_review_examples = {
        "auth-safety-evidence-pack.json",
        "auth-runtime-disabled-proof.json",
        "auth-traceability-matrix.json",
        "auth-no-go-regression-result.json",
    }
    for path in sorted((ROOT / "examples/auth").glob("*.json")):
        if path.name in aion_104_review_examples:
            continue
        if (
            path.name.startswith("local-session")
            or path.name == "role-aware-session-context.json"
            or "action-authorization" in path.name
            or "auth-runtime" in path.name
            or "mock-claims" in path.name
            or "production-auth" in path.name
            or path.name.startswith("request-identity-")
            or path.name.startswith("actor-context-")
            or path.name.startswith("offline-identity-")
            or path.name.startswith("identity-assertion-replay-")
            or path.name == "identity-assertion-identifier-collision.json"
            or path.name == "disabled-auth-prototype-plan.json"
        ):
            continue
        payload = json.loads(path.read_text())
        serialized = json.dumps(payload, sort_keys=True).lower()
        assert not any(item in serialized for item in blocked), path


def test_auth_design_check_script_passes() -> None:
    script = ROOT / "scripts/auth-design-check.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111
    subprocess.run([str(script)], cwd=ROOT, check=True)
