from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def test_production_auth_architecture_docs_exist() -> None:
    for path in [
        "docs/auth/production-auth-architecture.md",
        "docs/auth/auth-provider-evaluation-matrix.md",
        "docs/auth/identity-provider-boundary-model.md",
        "docs/auth/token-session-storage-decision.md",
        "docs/auth/credential-handling-no-go-rules.md",
        "docs/auth/production-auth-threat-model.md",
        "docs/auth/production-auth-release-gates.md",
        "docs/auth/disabled-auth-prototype-plan.md",
        "docs/adr/0089-production-auth-architecture-decision.md",
    ]:
        assert (ROOT / path).is_file()


def test_production_auth_architecture_boundaries_are_explicit() -> None:
    text = (ROOT / "docs/auth/production-auth-architecture.md").read_text()
    assert "No production auth is implemented in AION-098" in text
    assert "No provider integration is added in AION-098" in text
    assert "No credentials, tokens, sessions," in text
    assert "or cookies are created, stored, issued, or accepted" in text
    assert "`production_auth_enabled` remains false" in text
    assert "OIDC-compatible production auth" in text
    assert "reverse proxy auth" in text.lower()


def test_production_auth_adr_is_indexed() -> None:
    assert (ROOT / "docs/adr/0089-production-auth-architecture-decision.md").is_file()
    index = (ROOT / "docs/adr/README.md").read_text()
    assert "0089-production-auth-architecture-decision.md" in index


def test_production_auth_examples_are_synthetic_json() -> None:
    for path in [
        ROOT / "examples/auth/production-auth-provider-matrix.json",
        ROOT / "examples/auth/production-auth-threat-model.json",
        ROOT / "examples/auth/disabled-auth-prototype-plan.json",
        ROOT / "examples/auth/production-auth-release-gates.json",
    ]:
        payload = json.loads(path.read_text())
        assert payload["synthetic"] is True
        serialized = json.dumps(payload, sort_keys=True).lower()
        assert "sk-" not in serialized
        assert "ghp_" not in serialized
        assert "xoxb-" not in serialized
        assert "http://" not in serialized
        assert "https://" not in serialized


def test_production_auth_architecture_check_script_passes() -> None:
    script = ROOT / "scripts/production-auth-architecture-check.sh"
    assert script.is_file()
    assert script.stat().st_mode & 0o111
    subprocess.run([str(script)], cwd=ROOT, check=True)
