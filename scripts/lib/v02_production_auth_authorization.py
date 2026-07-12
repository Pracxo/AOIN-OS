#!/usr/bin/env python3
"""Validate the AION-151 scoped production-auth authorization record."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

TRANSACTION_ID = "AION-151-PA-0001"
CANDIDATE_ID = "production-auth-core"
WORKSTREAM = "production-auth-implementation"
IMPLEMENTATION_TASK = "AION-152"
AUTHORIZATION_SCOPE = "disabled-production-auth-core"

REQUIRED_DOCS = [
    "docs/release/v02-production-auth-implementation-authorization-transaction.md",
    "docs/release/v02-production-auth-explicit-approval-record.md",
    "docs/release/v02-production-auth-implementation-scope.md",
    "docs/release/v02-production-auth-runtime-guard-hold.md",
    "docs/release/v02-production-auth-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-authorization-no-go.md",
    "docs/release/v02-production-auth-authorization-checklist.md",
    "docs/adr/0142-v02-production-auth-implementation-authorization.md",
]

REQUIRED_JSON = [
    "examples/release/v02-production-auth-implementation-authorization.json",
    "examples/release/v02-production-auth-explicit-approval-record.json",
    "examples/release/v02-production-auth-runtime-guard-hold.json",
    "examples/release/v02-production-auth-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json",
]

TRUE_KEYS = {
    "authorization_transaction_approved",
    "explicit_approval_record_approval",
    "implementation_authorization_approved",
    "implementation_go_status",
}

CANONICAL_FALSE_KEYS = {
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

GLOBAL_FALSE_KEYS = (CANONICAL_FALSE_KEYS - {"implementation_no_go_status"}) | {
    "runtime_enablement_guard_release_approved",
    "runtime_enablement_master_lock_release_approved",
    "runtime_enablement_guard_final_lock_release_approved",
    "runtime_implementation_approved",
    "production_auth_runtime_enabled",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_dependency_added",
    "package_manager_file_added",
    "api_runtime_execution_route_added",
    "connector_runtime_enabled",
    "operator_write_execution_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "credentials_present",
    "tokens_present",
    "secrets_present",
}

REQUIRED_SCOPE = {
    "internal production-auth contracts",
    "internal production-auth configuration model",
    "disabled-by-default feature flags",
    "policy evaluation interfaces",
    "audit and provenance events",
    "redacted diagnostics",
    "deterministic test fixtures",
    "unit and integration tests",
    "documentation",
    "read-only static-console status evidence",
}

PROHIBITED_SCOPE = {
    "runtime enablement",
    "login endpoints",
    "logout endpoints",
    "authentication callback endpoints",
    "credential storage",
    "password storage",
    "token issuance",
    "token storage",
    "cookie or session persistence",
    "database migrations",
    "external identity providers",
    "network calls",
    "OAuth runtime",
    "OIDC runtime",
    "SAML runtime",
    "provider SDK installation",
    "frontend dependencies",
    "package or lockfile changes",
    "operator write execution",
    "connector runtime",
    "module activation",
    "sandbox execution",
    "production release or tag creation",
}

BLOCKED_VALUE_MARKERS = (
    "http://",
    "https://",
    "sk-",
    "ghp_",
    "xoxb-",
    "-----BEGIN PRIVATE KEY-----",
    "bearer ",
    "basic ",
    "api_key",
    "private_key",
    "client_secret",
    "access_token_value",
    "refresh_token_value",
    "id_token_value",
    "raw_prompt",
    "hidden_reasoning",
    "chain_of_thought",
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--mode", choices={"check", "no-go", "guard"}, default="check")
    args = parser.parse_args()
    root = args.repo_root.resolve()

    try:
        validate(root, args.mode)
    except AssertionError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


def validate(root: Path, mode: str) -> None:
    for relative in REQUIRED_DOCS + REQUIRED_JSON:
        assert (root / relative).exists(), f"missing AION-151 artifact: {relative}"

    adr_index = (root / "docs/adr/README.md").read_text()
    assert (
        "0142-v02-production-auth-implementation-authorization.md" in adr_index
    ), "ADR 0142 is not indexed"

    payloads = [(relative, load_json(root / relative)) for relative in REQUIRED_JSON]
    for relative, payload in payloads:
        validate_payload(relative, payload, require_canonical=True)

    approved_records: dict[tuple[str, str, str, str, str], set[str]] = {}
    for relative, payload in iter_json_payloads(root):
        collect_approval_record(relative, payload, approved_records)
        assert_global_false(relative, payload)
        assert_no_blocked_values(relative, payload)

    assert set(approved_records) == {
        (TRANSACTION_ID, CANDIDATE_ID, WORKSTREAM, IMPLEMENTATION_TASK, AUTHORIZATION_SCOPE)
    }, f"unexpected approved authorization records: {sorted(approved_records)}"

    if mode == "guard":
        for relative, payload in payloads:
            assert payload.get("runtime_guard_hold_active") is True, (
                f"{relative}: runtime_guard_hold_active must be true"
            )
            assert payload.get("runtime_no_go_status") is True, (
                f"{relative}: runtime_no_go_status must be true"
            )
            assert payload.get("production_auth_runtime_enabled") is False, (
                f"{relative}: production_auth_runtime_enabled must be false"
            )

    assert_no_forbidden_file_classes(root)


def validate_payload(relative: str, payload: dict[str, Any], *, require_canonical: bool) -> None:
    assert payload.get("task_id") == "AION-151", f"{relative}: task_id must be AION-151"
    assert payload.get("synthetic") is True, f"{relative}: synthetic must be true"
    assert payload.get("read_only") is True, f"{relative}: read_only must be true"
    assert payload.get("authorization_transaction_id") == TRANSACTION_ID, (
        f"{relative}: authorization_transaction_id mismatch"
    )
    assert payload.get("approval_record_id") == TRANSACTION_ID, (
        f"{relative}: approval_record_id mismatch"
    )
    assert payload.get("candidate_id") == CANDIDATE_ID, f"{relative}: candidate_id mismatch"
    assert payload.get("workstream") == WORKSTREAM, f"{relative}: workstream mismatch"
    assert payload.get("implementation_task") == IMPLEMENTATION_TASK, (
        f"{relative}: implementation_task mismatch"
    )
    assert payload.get("authorization_scope") == AUTHORIZATION_SCOPE, (
        f"{relative}: authorization_scope mismatch"
    )
    for key in TRUE_KEYS:
        assert payload.get(key) is True, f"{relative}: {key} must be true"
    for key in CANONICAL_FALSE_KEYS:
        assert payload.get(key) is False, f"{relative}: {key} must be false"
    assert payload.get("runtime_guard_hold_active") is True, (
        f"{relative}: runtime_guard_hold_active must be true"
    )
    assert payload.get("runtime_no_go_status") is True, (
        f"{relative}: runtime_no_go_status must be true"
    )
    assert REQUIRED_SCOPE <= set(payload.get("approved_scope", [])), (
        f"{relative}: approved_scope is incomplete"
    )
    assert PROHIBITED_SCOPE <= set(payload.get("prohibited_scope", [])), (
        f"{relative}: prohibited_scope is incomplete"
    )
    assert payload.get("required_adr") == "0142-v02-production-auth-implementation-authorization.md", (
        f"{relative}: required_adr mismatch"
    )
    assert payload.get("expiry") == "AION-152 merged or authorization explicitly revoked", (
        f"{relative}: expiry mismatch"
    )
    assert "revocation_path" in payload, f"{relative}: revocation_path missing"
    assert payload.get("reviewer_roles"), f"{relative}: reviewer_roles missing"
    assert payload.get("required_gates"), f"{relative}: required_gates missing"
    assert payload.get("evidence_references"), f"{relative}: evidence_references missing"
    if require_canonical:
        assert payload.get("record_kind") in {
            "authorization_transaction",
            "explicit_approval_record",
            "runtime_guard_hold",
            "authorization_evidence_matrix",
            "static_console_authorization",
            "static_console_runtime_guard_hold",
        }, f"{relative}: unexpected record_kind"


def collect_approval_record(
    relative: str,
    payload: Any,
    approved_records: dict[tuple[str, str, str, str, str], set[str]],
) -> None:
    if isinstance(payload, dict):
        true_keys = {key for key in TRUE_KEYS if payload.get(key) is True}
        if true_keys:
            assert true_keys == TRUE_KEYS, f"{relative}: partial authorization approval true keys"
            assert payload.get("approval_record_id") == TRANSACTION_ID, (
                f"{relative}: approved record id is not canonical"
            )
            assert payload.get("authorization_transaction_id") == TRANSACTION_ID, (
                f"{relative}: approved transaction id is not canonical"
            )
            assert payload.get("candidate_id") == CANDIDATE_ID, (
                f"{relative}: approved candidate is not canonical"
            )
            assert payload.get("workstream") == WORKSTREAM, (
                f"{relative}: approved workstream is not canonical"
            )
            assert payload.get("implementation_task") == IMPLEMENTATION_TASK, (
                f"{relative}: approved task is not canonical"
            )
            assert payload.get("authorization_scope") == AUTHORIZATION_SCOPE, (
                f"{relative}: approved scope is not canonical"
            )
            tuple_key = (
                payload["authorization_transaction_id"],
                payload["candidate_id"],
                payload["workstream"],
                payload["implementation_task"],
                payload["authorization_scope"],
            )
            approved_records.setdefault(tuple_key, set()).add(relative)
        for key, value in payload.items():
            collect_approval_record(f"{relative}:{key}", value, approved_records)
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            collect_approval_record(f"{relative}[{index}]", item, approved_records)


def assert_global_false(relative: str, value: Any) -> None:
    if isinstance(value, dict):
        for key, nested in value.items():
            if key in GLOBAL_FALSE_KEYS:
                assert nested is False, f"{relative}: {key} must remain false"
            assert_global_false(relative, nested)
    elif isinstance(value, list):
        for item in value:
            assert_global_false(relative, item)


def assert_no_blocked_values(relative: str, value: Any) -> None:
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_blocked_values(relative, nested)
    elif isinstance(value, list):
        for item in value:
            assert_no_blocked_values(relative, item)
    elif isinstance(value, str):
        lowered = value.lower()
        for marker in BLOCKED_VALUE_MARKERS:
            assert marker not in lowered, f"{relative}: blocked value marker {marker}"


def assert_no_forbidden_file_classes(root: Path) -> None:
    blocked_names = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb"}
    changed = run_git(root, "diff", "--name-only", "--diff-filter=ACMRT", "origin/main...HEAD")
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard")
    for name in [*changed, *untracked]:
        path = Path(name)
        assert path.name not in blocked_names, f"package or lockfile changed: {name}"
        assert "migrations" not in path.parts, f"migration path changed: {name}"
        assert not name.startswith("services/brain-api/src/aion_brain/api/"), (
            f"runtime API route changed: {name}"
        )
        assert not name.startswith("packages/aion-sdk-python/src/aion_sdk/resources/"), (
            f"SDK resource changed: {name}"
        )
        assert not name.startswith("packages/aion-sdk-python/src/aion_sdk/cli/commands/"), (
            f"CLI command changed: {name}"
        )


def iter_json_payloads(root: Path) -> list[tuple[str, Any]]:
    bases = [
        root / "examples/release",
        root / "examples/platform",
        root / "examples/auth",
        root / "examples/connectors",
        root / "examples/modules",
        root / "operator-console-static/demo-data",
    ]
    payloads: list[tuple[str, Any]] = []
    for base in bases:
        if not base.exists():
            continue
        for path in sorted(base.glob("*.json")):
            payloads.append((str(path.relative_to(root)), load_json(path)))
    return payloads


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict), f"{path}: JSON root must be an object"
    return payload


def run_git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
