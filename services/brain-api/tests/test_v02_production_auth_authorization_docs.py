"""AION-151 scoped production-auth authorization tests."""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]

DOCS = [
    "docs/release/v02-production-auth-implementation-authorization-transaction.md",
    "docs/release/v02-production-auth-explicit-approval-record.md",
    "docs/release/v02-production-auth-implementation-scope.md",
    "docs/release/v02-production-auth-runtime-guard-hold.md",
    "docs/release/v02-production-auth-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-authorization-no-go.md",
    "docs/release/v02-production-auth-authorization-checklist.md",
    "docs/adr/0142-v02-production-auth-implementation-authorization.md",
]

JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-implementation-authorization.json",
    "examples/release/v02-production-auth-explicit-approval-record.json",
    "examples/release/v02-production-auth-runtime-guard-hold.json",
    "examples/release/v02-production-auth-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json",
]

SCRIPTS = [
    "scripts/v02-production-auth-authorization-check.sh",
    "scripts/v02-production-auth-runtime-guard-hold.sh",
    "scripts/v02-production-auth-authorization-no-go-regression.sh",
]

TRUE_KEYS = {
    "authorization_transaction_approved",
    "explicit_approval_record_approval",
    "implementation_authorization_approved",
    "implementation_go_status",
}

FALSE_KEYS = {
    "implementation_no_go_status",
    "runtime_implementation_approved",
    "production_auth_runtime_enabled",
    "runtime_enablement_guard_release_approved",
    "runtime_enablement_guard_final_lock_release_approved",
    "runtime_enablement_master_lock_release_approved",
    "login_endpoint_approved",
    "logout_endpoint_approved",
    "callback_endpoint_approved",
    "credential_storage_approved",
    "password_storage_approved",
    "token_storage_approved",
    "session_storage_approved",
    "cookie_session_persistence_approved",
    "external_identity_provider_approved",
    "oauth_runtime_approved",
    "oidc_runtime_approved",
    "saml_runtime_approved",
    "external_calls_approved",
    "network_client_approved",
    "provider_sdk_approved",
    "operator_write_execution_approved",
    "connector_implementation_approved",
    "connector_runtime_enabled",
    "module_activation_approved",
    "sandbox_execution_approved",
    "package_files_added",
    "lockfiles_added",
    "migrations_added",
    "runtime_api_routes_added",
    "v02_tag_created",
    "v02_release_created",
    "v02_release_approved",
}


def test_v02_production_auth_authorization_docs_exist_and_define_scope() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative
    assert "0142-v02-production-auth-implementation-authorization.md" in _text(
        "docs/adr/README.md"
    )

    transaction = _text(
        "docs/release/v02-production-auth-implementation-authorization-transaction.md"
    )
    for required in [
        "## Purpose",
        "## Scope",
        "## Governance prerequisite",
        "## AION-150 baseline",
        "## Candidate",
        "## Authorization transaction ID",
        "## Approval record ID",
        "## Authorized future task",
        "## Authorized implementation scope",
        "## Prohibited implementation scope",
        "## Runtime guard state",
        "## Expiry",
        "## Revocation",
        "## Required evidence",
        "## Required reviewers",
        "## No-go conditions",
        "AION-151 implements no runtime code",
        "creates no v0.2 tag or release",
    ]:
        assert required in transaction

    approval = _text("docs/release/v02-production-auth-explicit-approval-record.md")
    for required in [
        "authorization_transaction_id=AION-151-PA-0001",
        "approval_record_id=AION-151-PA-0001",
        "candidate_id=production-auth-core",
        "workstream=production-auth-implementation",
        "implementation_task=AION-152",
        "authorization_transaction_approved=true",
        "explicit_approval_record_approval=true",
        "implementation_authorization_approved=true",
        "implementation_go_status=true",
        "implementation_no_go_status=false",
        "runtime_no_go_status=true",
        "runtime_implementation_approved=false",
        "production_auth_runtime_enabled=false",
        "runtime_enablement_guard_release_approved=false",
        "runtime_enablement_master_lock_release_approved=false",
    ]:
        assert required in approval


def test_v02_production_auth_authorization_json_is_exactly_scoped() -> None:
    approved_tuples: set[tuple[str, str, str, str, str]] = set()
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-151"
        assert payload["synthetic"] is True
        assert payload["read_only"] is True
        assert payload["authorization_transaction_id"] == "AION-151-PA-0001"
        assert payload["approval_record_id"] == "AION-151-PA-0001"
        assert payload["candidate_id"] == "production-auth-core"
        assert payload["workstream"] == "production-auth-implementation"
        assert payload["implementation_task"] == "AION-152"
        assert payload["authorization_scope"] == "disabled-production-auth-core"
        for key in TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert payload["runtime_guard_hold_active"] is True
        assert payload["runtime_no_go_status"] is True
        assert payload["required_adr"] == "0142-v02-production-auth-implementation-authorization.md"
        assert payload["required_gates"]
        assert payload["evidence_references"]
        assert payload["reviewer_roles"]
        assert payload["expiry"] == "AION-152 merged or authorization explicitly revoked"
        assert payload["revocation_path"]
        approved_tuples.add(
            (
                payload["authorization_transaction_id"],
                payload["candidate_id"],
                payload["workstream"],
                payload["implementation_task"],
                payload["authorization_scope"],
            )
        )
    assert approved_tuples == {
        (
            "AION-151-PA-0001",
            "production-auth-core",
            "production-auth-implementation",
            "AION-152",
            "disabled-production-auth-core",
        )
    }


def test_v02_production_auth_authorization_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["AION_V02_PRODUCTION_AUTH_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK"] = "1"
    env["PYTEST_CURRENT_TEST"] = env.get(
        "PYTEST_CURRENT_TEST", "AION-151 focused script test"
    )
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
