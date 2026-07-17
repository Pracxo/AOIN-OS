"""AION-160 actor-context trust-boundary release artifact tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/auth/actor-context-trust-boundary.md",
    "docs/auth/development-identity-simulation.md",
    "docs/release/v02-actor-context-trust-boundary-remediation.md",
    "docs/release/v02-actor-context-trust-boundary-runtime-hold.md",
    "docs/release/v02-actor-context-trust-boundary-evidence-matrix.md",
    "docs/release/v02-actor-context-trust-boundary-no-go.md",
    "docs/release/v02-actor-context-trust-boundary-checklist.md",
    "docs/adr/0151-v02-actor-context-trust-boundary-remediation.md",
]

JSON_ARTIFACTS = [
    "examples/auth/actor-context-anonymous-resolution.json",
    "examples/auth/actor-context-request-identity-resolution.json",
    "examples/auth/actor-context-development-simulation.json",
    "examples/auth/actor-context-resolution-audit-event.json",
    "examples/auth/actor-context-resolution-provenance.json",
    "examples/auth/actor-context-resolution-diagnostics.json",
    "operator-console-static/demo-data/actor-context-trust-boundary.json",
    "operator-console-static/demo-data/actor-context-runtime-hold.json",
]

SCRIPTS = [
    "scripts/production-auth-actor-context-trust-boundary-no-go-regression.sh",
    "scripts/production-auth-actor-context-trust-boundary-check.sh",
    "scripts/production-auth-actor-context-trust-boundary-runtime-hold.sh",
]

REQUIRED_FALSE = [
    "authenticated_actor_context_enabled",
    "identity_verification_enabled",
    "authenticated_requests_enabled",
    "production_auth_runtime_enabled",
    "production_actor_header_trust_enabled",
    "production_workspace_header_trust_enabled",
    "production_role_header_trust_enabled",
    "production_permission_header_trust_enabled",
    "production_security_scope_header_trust_enabled",
    "authorization_header_parsing_enabled",
    "cookie_parsing_enabled",
    "credential_verification_enabled",
    "password_verification_enabled",
    "token_parsing_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "token_refresh_enabled",
    "session_creation_enabled",
    "session_storage_enabled",
    "cookie_issuance_enabled",
    "cookie_session_persistence_enabled",
    "external_identity_provider_enabled",
    "oauth_runtime_enabled",
    "oidc_runtime_enabled",
    "saml_runtime_enabled",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_enabled",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "token_endpoint_enabled",
    "session_endpoint_enabled",
    "credential_endpoint_enabled",
    "openapi_security_scheme_added",
    "runtime_api_routes_added",
    "sdk_runtime_resource_added",
    "cli_runtime_command_added",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "v02_tag_created",
    "v02_release_created",
]


def test_aion160_required_files_exist_and_status_is_current() -> None:
    for relative in DOCS + JSON_ARTIFACTS + SCRIPTS:
        assert (ROOT / relative).exists(), relative
    assert "0151-v02-actor-context-trust-boundary-remediation.md" in _text(
        "docs/adr/README.md"
    )

    status = _text("docs/project-status.md")
    assert (
        "AION-160 actor-context trust-boundary remediation implemented" in status
        or "Current authorization: AION-161-PA-0006 active for AION-162." in status
        or "Current authorization: AION-161-PA-0006 consumed by AION-162 when merged."
        in status
    )
    assert "non-development identity headers ignored" in status
    assert "anonymous zero-permission ActorContext" in status
    assert "RequestIdentityContext precedence" in status
    assert "RequestContext trace/correlation projection" in status
    assert "development simulation isolated" in status
    assert "production authentication disabled" in status
    assert (
        "Formal lifecycle closeout: AION-161." in status
        or (
            "Next implementation task: AION-162 offline Ed25519 identity assertion "
            "verification core."
        )
        in status
    )


def test_aion160_json_artifacts_are_synthetic_read_only_and_fail_closed() -> None:
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True
        assert payload["actor_context_trust_boundary_remediated"] is True
        assert payload["actor_context_resolution_state"] == "implemented_fail_closed"
        assert payload["authorization_transaction_id"] == "AION-159-PA-0005"
        assert payload["implementation_task"] == "AION-160"
        assert payload["authorization_scope"] == "fail-closed-actor-context-resolution"

    anonymous = _json("examples/auth/actor-context-anonymous-resolution.json")
    assert anonymous["actor_context_source"] == "anonymous_fail_closed"
    assert anonymous["actor_id"] is None
    assert anonymous["workspace_id"] is None
    assert anonymous["roles"] == []
    assert anonymous["permissions"] == []
    assert anonymous["security_scope"] == []
    assert anonymous["dev_mode"] is False

    request_identity = _json("examples/auth/actor-context-request-identity-resolution.json")
    assert request_identity["actor_context_source"] == "request_identity_disabled"
    assert "request_identity_context_disabled" in request_identity["reason_codes"]

    runtime_hold = _json("operator-console-static/demo-data/actor-context-runtime-hold.json")
    assert runtime_hold["runtime_guard_hold_active"] is True
    assert runtime_hold["runtime_no_go_status"] is True
    for key in REQUIRED_FALSE:
        assert runtime_hold[key] is False, key


def test_aion160_scripts_are_executable_and_pass_from_pytest() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-160 script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()


def _json(relative: str) -> dict[str, object]:
    return json.loads((ROOT / relative).read_text())
