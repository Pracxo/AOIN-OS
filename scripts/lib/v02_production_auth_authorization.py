#!/usr/bin/env python3
"""Validate production-auth authorization lifecycle records."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuthorizationSpec:
    transaction_id: str
    approval_record_id: str
    candidate_id: str
    workstream: str
    implementation_task: str
    authorization_scope: str
    task_id: str
    required_adr: str
    expiry: str
    authorization_active: bool
    authorization_consumed: bool
    authorization_expired: bool
    authorization_reusable: bool
    parent_authorization_transaction_id: str | None = None
    authorization_consumed_by_task: str | None = None
    authorization_consumed_by_pr: int | None = None
    authorization_consumed_by_merge_commit: str | None = None

    @property
    def tuple_key(self) -> tuple[str, str, str, str, str]:
        return (
            self.transaction_id,
            self.candidate_id,
            self.workstream,
            self.implementation_task,
            self.authorization_scope,
        )


AION_152_MERGE_COMMIT = "bc0614bcde19448b2a423614836bee3c06728c98"

HISTORICAL_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-151-PA-0001",
    approval_record_id="AION-151-PA-0001",
    candidate_id="production-auth-core",
    workstream="production-auth-implementation",
    implementation_task="AION-152",
    authorization_scope="disabled-production-auth-core",
    task_id="AION-151",
    required_adr="0142-v02-production-auth-implementation-authorization.md",
    expiry="AION-152 merged; authorization consumed by PR 62",
    authorization_active=False,
    authorization_consumed=True,
    authorization_expired=True,
    authorization_reusable=False,
    authorization_consumed_by_task="AION-152",
    authorization_consumed_by_pr=62,
    authorization_consumed_by_merge_commit=AION_152_MERGE_COMMIT,
)

ACTIVE_AUTHORIZATION = AuthorizationSpec(
    transaction_id="AION-153-PA-0002",
    approval_record_id="AION-153-PA-0002",
    candidate_id="production-auth-core-stabilization",
    workstream="production-auth-hardening",
    implementation_task="AION-154",
    authorization_scope="disabled-production-auth-core-stabilization",
    task_id="AION-153",
    required_adr="0144-v02-production-auth-core-stabilization-authorization.md",
    expiry="AION-154 merged or authorization explicitly revoked",
    authorization_active=True,
    authorization_consumed=False,
    authorization_expired=False,
    authorization_reusable=False,
    parent_authorization_transaction_id="AION-151-PA-0001",
)

AUTHORIZATION_SPECS = {
    HISTORICAL_AUTHORIZATION.transaction_id: HISTORICAL_AUTHORIZATION,
    ACTIVE_AUTHORIZATION.transaction_id: ACTIVE_AUTHORIZATION,
}

APPROVAL_TRUE_KEYS = {
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
    "production_auth_enabled",
    "auth_runtime_enabled",
    "external_calls_enabled",
    "network_client_enabled",
    "provider_sdk_dependency_added",
    "provider_sdk_enabled",
    "package_manager_file_added",
    "api_runtime_execution_route_added",
    "connector_runtime_enabled",
    "connector_activation_enabled",
    "operator_write_execution_enabled",
    "module_activation_enabled",
    "sandbox_execution_enabled",
    "credentials_present",
    "tokens_present",
    "secrets_present",
    "credential_values_present",
    "token_values_present",
    "login_endpoint_enabled",
    "logout_endpoint_enabled",
    "callback_endpoint_enabled",
    "credential_storage_enabled",
    "password_storage_enabled",
    "token_issuance_enabled",
    "token_storage_enabled",
    "session_creation_enabled",
    "session_storage_enabled",
    "cookie_issuance_enabled",
    "cookie_session_persistence_enabled",
    "external_identity_provider_enabled",
    "oauth_runtime_enabled",
    "oidc_runtime_enabled",
    "saml_runtime_enabled",
}

HISTORICAL_REQUIRED_SCOPE = {
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

ACTIVE_REQUIRED_SCOPE = {
    "internal production-auth core stabilization",
    "disabled-by-default configuration hardening",
    "fail-closed policy stabilization",
    "audit and provenance evidence stabilization",
    "redacted diagnostics stabilization",
    "deterministic stabilization tests",
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

REQUIRED_DOCS_AION151 = [
    "docs/release/v02-production-auth-implementation-authorization-transaction.md",
    "docs/release/v02-production-auth-explicit-approval-record.md",
    "docs/release/v02-production-auth-implementation-scope.md",
    "docs/release/v02-production-auth-runtime-guard-hold.md",
    "docs/release/v02-production-auth-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-authorization-no-go.md",
    "docs/release/v02-production-auth-authorization-checklist.md",
    "docs/adr/0142-v02-production-auth-implementation-authorization.md",
]

REQUIRED_JSON_AION151 = [
    "examples/release/v02-production-auth-implementation-authorization.json",
    "examples/release/v02-production-auth-explicit-approval-record.json",
    "examples/release/v02-production-auth-runtime-guard-hold.json",
    "examples/release/v02-production-auth-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-authorization.json",
    "operator-console-static/demo-data/v02-production-auth-runtime-guard-hold.json",
]

REQUIRED_DOCS_AION153 = [
    "docs/release/v02-production-auth-core-implementation-closeout.md",
    "docs/release/v02-production-auth-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-stabilization-scope.md",
    "docs/release/v02-production-auth-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-stabilization-authorization-evidence-matrix.md",
    "docs/release/v02-production-auth-stabilization-authorization-no-go.md",
    "docs/release/v02-production-auth-stabilization-authorization-checklist.md",
    "docs/adr/0144-v02-production-auth-core-stabilization-authorization.md",
]

REQUIRED_JSON_AION153 = [
    "examples/release/v02-production-auth-core-implementation-closeout.json",
    "examples/release/v02-production-auth-stabilization-authorization.json",
    "examples/release/v02-production-auth-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json",
    "operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json",
]

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
    for relative in (
        REQUIRED_DOCS_AION151
        + REQUIRED_JSON_AION151
        + REQUIRED_DOCS_AION153
        + REQUIRED_JSON_AION153
    ):
        assert (root / relative).exists(), f"missing production-auth authorization artifact: {relative}"

    adr_index = (root / "docs/adr/README.md").read_text()
    assert "0142-v02-production-auth-implementation-authorization.md" in adr_index, (
        "ADR 0142 is not indexed"
    )
    assert "0144-v02-production-auth-core-stabilization-authorization.md" in adr_index, (
        "ADR 0144 is not indexed"
    )

    for relative in REQUIRED_JSON_AION151 + REQUIRED_JSON_AION153:
        validate_required_payload(relative, load_json(root / relative))

    validate_authorization_lifecycle_payloads(iter_json_payloads(root))

    if mode == "guard":
        for relative in REQUIRED_JSON_AION151 + REQUIRED_JSON_AION153:
            payload = load_json(root / relative)
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


def validate_required_payload(relative: str, payload: dict[str, Any]) -> None:
    assert payload.get("synthetic") is True, f"{relative}: synthetic must be true"
    assert payload.get("read_only") is True, f"{relative}: read_only must be true"
    assert payload.get("record_kind"), f"{relative}: record_kind missing"

    if relative in REQUIRED_JSON_AION151:
        validate_authorization_record(relative, payload, expected=HISTORICAL_AUTHORIZATION)
    elif relative.endswith("v02-production-auth-core-implementation-closeout.json"):
        assert payload.get("task_id") == "AION-153", f"{relative}: task_id must be AION-153"
        consumed = payload.get("consumed_authorization_record")
        assert isinstance(consumed, dict), f"{relative}: consumed authorization record missing"
        validate_authorization_record(
            f"{relative}:consumed_authorization_record",
            consumed,
            expected=HISTORICAL_AUTHORIZATION,
        )
    else:
        validate_authorization_record(relative, payload, expected=ACTIVE_AUTHORIZATION)


def validate_authorization_lifecycle_payloads(payloads: list[tuple[str, Any]]) -> None:
    approved_records: dict[tuple[str, str, str, str, str], set[str]] = {}
    active_records: dict[tuple[str, str, str, str, str], set[str]] = {}
    historical_records: dict[tuple[str, str, str, str, str], set[str]] = {}

    for relative, payload in payloads:
        collect_approval_record(relative, payload, approved_records, active_records, historical_records)
        assert_global_false(relative, payload)
        assert_no_blocked_values(relative, payload)

    expected_records = {HISTORICAL_AUTHORIZATION.tuple_key, ACTIVE_AUTHORIZATION.tuple_key}
    assert set(approved_records) == expected_records, (
        f"unexpected approved authorization records: {sorted(approved_records)}"
    )
    assert set(active_records) == {ACTIVE_AUTHORIZATION.tuple_key}, (
        f"unexpected active approved authorization records: {sorted(active_records)}"
    )
    assert HISTORICAL_AUTHORIZATION.tuple_key in historical_records, (
        "AION-151 historical authorization record missing"
    )


def validate_authorization_record(
    relative: str,
    payload: dict[str, Any],
    *,
    expected: AuthorizationSpec | None = None,
) -> AuthorizationSpec:
    true_keys = {key for key in APPROVAL_TRUE_KEYS if payload.get(key) is True}
    assert true_keys == APPROVAL_TRUE_KEYS, f"{relative}: partial authorization approval true keys"

    transaction_id = payload.get("authorization_transaction_id")
    assert isinstance(transaction_id, str), f"{relative}: authorization_transaction_id missing"
    spec = expected or AUTHORIZATION_SPECS.get(transaction_id)
    assert spec is not None, f"{relative}: unknown approved authorization record {transaction_id}"
    assert transaction_id == spec.transaction_id, f"{relative}: authorization_transaction_id mismatch"
    assert payload.get("approval_record_id") == spec.approval_record_id, (
        f"{relative}: approval_record_id mismatch"
    )
    assert payload.get("candidate_id") == spec.candidate_id, f"{relative}: candidate_id mismatch"
    assert payload.get("workstream") == spec.workstream, f"{relative}: workstream mismatch"
    assert payload.get("implementation_task") == spec.implementation_task, (
        f"{relative}: implementation_task mismatch"
    )
    assert payload.get("authorization_scope") == spec.authorization_scope, (
        f"{relative}: authorization_scope mismatch"
    )
    assert payload.get("task_id") == spec.task_id, f"{relative}: task_id mismatch"

    for key in CANONICAL_FALSE_KEYS:
        assert payload.get(key) is False, f"{relative}: {key} must be false"
    assert payload.get("runtime_guard_hold_active") is True, (
        f"{relative}: runtime_guard_hold_active must be true"
    )
    assert payload.get("runtime_no_go_status") is True, (
        f"{relative}: runtime_no_go_status must be true"
    )

    assert payload.get("authorization_active") is spec.authorization_active, (
        f"{relative}: authorization_active must be {str(spec.authorization_active).lower()}"
    )
    assert payload.get("authorization_consumed") is spec.authorization_consumed, (
        f"{relative}: authorization_consumed must be {str(spec.authorization_consumed).lower()}"
    )
    assert payload.get("authorization_expired") is spec.authorization_expired, (
        f"{relative}: authorization_expired must be {str(spec.authorization_expired).lower()}"
    )
    assert payload.get("authorization_reusable") is spec.authorization_reusable, (
        f"{relative}: authorization_reusable must be {str(spec.authorization_reusable).lower()}"
    )
    assert payload.get("parent_authorization_transaction_id") == spec.parent_authorization_transaction_id, (
        f"{relative}: parent_authorization_transaction_id mismatch"
    )

    if spec.authorization_consumed:
        assert payload.get("authorization_consumed_by_task") == spec.authorization_consumed_by_task, (
            f"{relative}: authorization_consumed_by_task mismatch"
        )
        assert payload.get("authorization_consumed_by_pr") == spec.authorization_consumed_by_pr, (
            f"{relative}: authorization_consumed_by_pr mismatch"
        )
        assert (
            payload.get("authorization_consumed_by_merge_commit")
            == spec.authorization_consumed_by_merge_commit
        ), f"{relative}: authorization_consumed_by_merge_commit mismatch"
    else:
        assert payload.get("authorization_consumed_by_task") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by task"
        )
        assert payload.get("authorization_consumed_by_pr") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by PR"
        )
        assert payload.get("authorization_consumed_by_merge_commit") in {None, ""}, (
            f"{relative}: active authorization must not be consumed by merge commit"
        )

    required_scope = (
        ACTIVE_REQUIRED_SCOPE
        if spec.transaction_id == ACTIVE_AUTHORIZATION.transaction_id
        else HISTORICAL_REQUIRED_SCOPE
    )
    assert required_scope <= set(payload.get("approved_scope", [])), (
        f"{relative}: approved_scope is incomplete"
    )
    assert PROHIBITED_SCOPE <= set(payload.get("prohibited_scope", [])), (
        f"{relative}: prohibited_scope is incomplete"
    )
    assert payload.get("required_adr") == spec.required_adr, f"{relative}: required_adr mismatch"
    assert payload.get("expiry") == spec.expiry, f"{relative}: expiry mismatch"
    assert "revocation_path" in payload, f"{relative}: revocation_path missing"
    assert payload.get("reviewer_roles"), f"{relative}: reviewer_roles missing"
    assert payload.get("required_gates"), f"{relative}: required_gates missing"
    assert payload.get("evidence_references"), f"{relative}: evidence_references missing"
    return spec


def collect_approval_record(
    relative: str,
    payload: Any,
    approved_records: dict[tuple[str, str, str, str, str], set[str]],
    active_records: dict[tuple[str, str, str, str, str], set[str]],
    historical_records: dict[tuple[str, str, str, str, str], set[str]],
) -> None:
    if isinstance(payload, dict):
        true_keys = {key for key in APPROVAL_TRUE_KEYS if payload.get(key) is True}
        if true_keys:
            spec = validate_authorization_record(relative, payload)
            approved_records.setdefault(spec.tuple_key, set()).add(relative)
            if payload.get("authorization_active") is True:
                active_records.setdefault(spec.tuple_key, set()).add(relative)
            else:
                historical_records.setdefault(spec.tuple_key, set()).add(relative)
        elif true_keys != APPROVAL_TRUE_KEYS and true_keys:
            raise AssertionError(f"{relative}: partial authorization approval true keys")
        for key, value in payload.items():
            collect_approval_record(
                f"{relative}:{key}",
                value,
                approved_records,
                active_records,
                historical_records,
            )
    elif isinstance(payload, list):
        for index, item in enumerate(payload):
            collect_approval_record(
                f"{relative}[{index}]",
                item,
                approved_records,
                active_records,
                historical_records,
            )


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
    changed = run_git_diff(root)
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard")
    for name in [*changed, *untracked]:
        path = Path(name)
        assert path.name not in blocked_names, f"package or lockfile changed: {name}"
        assert "migrations" not in path.parts, f"migration path changed: {name}"
        assert not name.startswith("services/brain-api/src/aion_brain/api/"), (
            f"runtime API route changed: {name}"
        )
        assert not name.startswith("packages/aion-sdk-python/src/"), (
            f"SDK or CLI source changed: {name}"
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


def run_git_diff(root: Path) -> list[str]:
    base = comparison_base(root)
    args = ["diff", "--name-only", "--diff-filter=ACMRT"]
    if base:
        args.extend([base, "HEAD"])
    return run_git(root, *args)


def comparison_base(root: Path) -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])

    for candidate in candidates:
        if git_ref_exists(root, candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if git_ref_exists(root, "HEAD~1"):
        return "HEAD~1"
    return None


def git_ref_exists(root: Path, ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


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
