"""AION-157 request identity stabilization authorization tests."""

from __future__ import annotations

import copy
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from v02_production_auth_authorization import (  # noqa: E402
    AION151_AUTHORIZATION,
    AION153_AUTHORIZATION,
    AION155_AUTHORIZATION,
    AION157_AUTHORIZATION,
    AION159_AUTHORIZATION,
    AION161_AUTHORIZATION,
    APPROVAL_TRUE_KEYS,
    REQUEST_BOUNDARY_IMPLEMENTATION_TRUE_KEYS,
    REQUEST_IDENTITY_STABILIZATION_FALSE_KEYS,
    REQUEST_IDENTITY_STABILIZATION_PROHIBITED_SCOPE,
    REQUEST_IDENTITY_STABILIZATION_TRUE_KEYS,
    validate_authorization_lifecycle_payloads,
)

AION156_FEATURE_COMMIT = "2fbeb77bdc33772c46a679cbfa0bdafe327abb42"
AION156_MERGE_COMMIT = "051f6f2e8b901863f8dc9cad405e5b5401db3695"
AION158_FEATURE_COMMIT = "767fd9b228b00b04569df2e3b1b3f6bc9ecd846f"
AION158_MERGE_COMMIT = "f792c92e1d8a73ec8e7377b5d59269dea359006d"

DOCS = [
    "docs/release/v02-production-auth-request-identity-boundary-closeout.md",
    "docs/release/v02-production-auth-request-identity-stabilization-authorization-transaction.md",
    "docs/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.md",
    "docs/release/v02-production-auth-request-identity-stabilization-scope.md",
    "docs/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.md",
    "docs/release/v02-production-auth-request-identity-stabilization-evidence-matrix.md",
    "docs/release/v02-production-auth-request-identity-stabilization-no-go.md",
    "docs/release/v02-production-auth-request-identity-stabilization-checklist.md",
    "docs/adr/0148-v02-production-auth-request-identity-stabilization-authorization.md",
]

AION155_JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-request-boundary-authorization.json",
    "examples/release/v02-production-auth-request-boundary-runtime-hold.json",
    "operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json",
]

AION157_JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-request-identity-stabilization-authorization.json",
    "examples/release/v02-production-auth-request-identity-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-request-identity-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-request-identity-stabilization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-request-identity-stabilization-authorization.json",
]

JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-request-identity-boundary-closeout.json",
    *AION155_JSON_ARTIFACTS,
    *AION157_JSON_ARTIFACTS,
]

SCRIPTS = [
    "scripts/v02-production-auth-request-identity-stabilization-authorization-no-go-regression.sh",
    "scripts/v02-production-auth-request-identity-stabilization-authorization-check.sh",
]

PROTECTED_SOURCE_PATHS = [
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/production_auth",
    "services/brain-api/src/aion_brain/api_support",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel",
    "services/brain-api/src/aion_brain/api",
    "packages/aion-sdk-python/src",
]

AION160_ALLOWED_CHANGED_PATHS = {
    "services/brain-api/src/aion_brain/contracts/actor_context_resolution.py",
    "services/brain-api/src/aion_brain/identity/dev_auth.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/actor_context.py",
    "services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
}

AION162_ALLOWED_CHANGED_PATHS = {
    "services/brain-api/pyproject.toml",
    "services/brain-api/src/aion_brain/contracts/identity_assertion.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py",
    "services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py",
}


def test_aion157_required_files_exist_and_status_is_current() -> None:
    for relative in DOCS + JSON_ARTIFACTS + SCRIPTS:
        assert (ROOT / relative).exists(), relative
    assert "0148-v02-production-auth-request-identity-stabilization-authorization.md" in _text(
        "docs/adr/README.md"
    )

    status = _text("docs/project-status.md")
    assert (
        "Current milestone: AION-158 request-identity stabilization merged." in status
        or "Current milestone: AION-160 actor-context trust-boundary remediation implemented."
        in status
        or "Current milestone: AION-160 actor-context trust-boundary remediation merged."
        in status
        or (
            "Current milestone: AION-162 offline Ed25519 identity assertion verification "
            "core implemented."
        )
        in status
    )
    assert any(
        marker in status
        for marker in (
            "Current authorization: AION-159-PA-0005 active for AION-160.",
            "Current authorization: AION-159-PA-0005 consumed by AION-160 when merged.",
            "Current authorization: AION-161-PA-0006 active for AION-162.",
            "Current authorization: AION-161-PA-0006 consumed by AION-162 when merged.",
        )
    )
    assert (
        "Next task: AION-160 actor-context trust-boundary remediation." in status
        or "Formal lifecycle closeout: AION-161." in status
        or "Next task: AION-162 offline identity assertion verification core." in status
        or "Formal lifecycle closeout: AION-163." in status
    )

    readiness = _text("docs/release/v02-release-readiness-delta.md")
    assert "Disabled request identity boundary" in readiness
    assert "Request identity implementation evidence" in readiness
    assert "Request identity stabilization" in readiness
    assert (
        "`AION-160` is the next critical path" in readiness
        or "AION-160 remediates the actor-context trust boundary" in readiness
        or "`AION-162` is the next critical path" in readiness
    )
    assert "`v02_release_ready=false`" in readiness
    assert "`v02_tag_created=false`" in readiness
    assert "`v02_release_created=false`" in readiness


def test_aion157_json_is_valid_synthetic_read_only_and_exactly_scoped() -> None:
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True

    closeout = _json("examples/release/v02-production-auth-request-identity-boundary-closeout.json")
    assert closeout["task_id"] == "AION-157"
    assert closeout["record_kind"] == "request_identity_boundary_closeout"
    assert closeout["authorization_transaction_id"] == "AION-155-PA-0003"
    assert closeout["authorization_active"] is False
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_consumed_by_task"] == "AION-156"
    assert closeout["authorization_consumed_by_pr"] == 66
    assert closeout["authorization_consumed_by_feature_commit"] == AION156_FEATURE_COMMIT
    assert closeout["authorization_consumed_by_merge_commit"] == AION156_MERGE_COMMIT
    assert closeout["authorization_expired"] is True
    assert closeout["authorization_reusable"] is False
    assert closeout["request_identity_boundary_implemented"] is True
    assert closeout["request_identity_boundary_state"] == "implemented_disabled"
    assert closeout["request_identity_boundary_default_enabled"] is False
    assert closeout["request_identity_boundary_mode"] == "observe_only_disabled"
    assert closeout["authentication_state"] == "disabled"
    assert closeout["authenticated"] is False
    assert closeout["actor_id"] is None
    assert closeout["subject"] is None
    assert closeout["roles"] == []
    assert closeout["runtime_effect"] is False

    for relative in AION155_JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-155"
        assert payload["authorization_transaction_id"] == "AION-155-PA-0003"
        assert payload["approval_record_id"] == "AION-155-PA-0003"
        assert payload["parent_authorization_transaction_id"] == "AION-153-PA-0002"
        assert payload["candidate_id"] == "production-auth-request-identity-boundary"
        assert payload["workstream"] == "production-auth-request-integration"
        assert payload["implementation_task"] == "AION-156"
        assert payload["authorization_scope"] == "disabled-request-identity-boundary"
        assert payload["authorization_active"] is False
        assert payload["authorization_consumed"] is True
        assert payload["authorization_consumed_by_task"] == "AION-156"
        assert payload["authorization_consumed_by_pr"] == 66
        assert payload["authorization_consumed_by_feature_commit"] == AION156_FEATURE_COMMIT
        assert payload["authorization_consumed_by_merge_commit"] == AION156_MERGE_COMMIT
        assert payload["authorization_expired"] is True
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS | REQUEST_BOUNDARY_IMPLEMENTATION_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"

    for relative in AION157_JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-157"
        assert payload["authorization_transaction_id"] == "AION-157-PA-0004"
        assert payload["approval_record_id"] == "AION-157-PA-0004"
        assert payload["parent_authorization_transaction_id"] == "AION-155-PA-0003"
        assert payload["candidate_id"] == "production-auth-request-identity-boundary-stabilization"
        assert payload["workstream"] == "production-auth-request-integration-hardening"
        assert payload["implementation_task"] == "AION-158"
        assert payload["authorization_scope"] == "disabled-request-identity-boundary-stabilization"
        assert payload["authorization_active"] is False
        assert payload["authorization_consumed"] is True
        assert payload["authorization_consumed_by_task"] == "AION-158"
        assert payload["authorization_consumed_by_pr"] == 68
        assert payload["authorization_consumed_by_feature_commit"] == AION158_FEATURE_COMMIT
        assert payload["authorization_consumed_by_merge_commit"] == AION158_MERGE_COMMIT
        assert payload["authorization_expired"] is True
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS | REQUEST_IDENTITY_STABILIZATION_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in REQUEST_IDENTITY_STABILIZATION_FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert set(payload["approved_scope"]) == AION157_AUTHORIZATION.approved_scope
        assert set(payload["prohibited_scope"]) == REQUEST_IDENTITY_STABILIZATION_PROHIBITED_SCOPE
        assert payload["required_adr"] == AION157_AUTHORIZATION.required_adr
        assert payload["expiry"] == AION157_AUTHORIZATION.expiry


def test_aion157_validator_accepts_exact_six_record_lifecycle() -> None:
    validate_authorization_lifecycle_payloads(_canonical_records())


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records.append(
                (
                    "duplicate-active.json",
                    _payload_from_spec(AION155_AUTHORIZATION)
                    | {"authorization_active": True},
                )
            ),
            "authorization_active must be false",
        ),
        (
            lambda records: records.append(("unknown.json", _unknown_active_payload())),
            "unknown approved authorization record",
        ),
        (
            lambda records: records[2][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("authorization_reusable", True),
            "authorization_reusable must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("authorization_expired", False),
            "authorization_expired must be true",
        ),
        (
            lambda records: records[3][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[3][1].__setitem__("authorization_reusable", True),
            "authorization_reusable must be false",
        ),
        (
            lambda records: records[3][1].__setitem__("authorization_expired", False),
            "authorization_expired must be true",
        ),
        (
            lambda records: records[5][1].__setitem__("authorization_consumed", True),
            "authorization_consumed must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("authorization_expired", True),
            "authorization_expired must be false",
        ),
        (
            lambda records: records[5][1].__setitem__(
                "parent_authorization_transaction_id",
                "AION-153-PA-0002",
            ),
            "parent_authorization_transaction_id mismatch",
        ),
        (
            lambda records: records[5][1].__setitem__("implementation_task", "AION-157"),
            "implementation_task mismatch",
        ),
        (
            lambda records: records[5][1].__setitem__("candidate_id", "production-auth-runtime"),
            "candidate_id mismatch",
        ),
        (
            lambda records: records[5][1].__setitem__("workstream", "production-auth-runtime"),
            "workstream mismatch",
        ),
        (
            lambda records: records[5][1].__setitem__(
                "authorization_scope",
                "disabled-request-identity-boundary-stabilization-and-login",
            ),
            "authorization_scope mismatch",
        ),
        (
            lambda records: records[5][1].__setitem__(
                "offline_identity_assertion_verifier_approved",
                False,
            ),
            "offline_identity_assertion_verifier_approved must be true",
        ),
        (
            lambda records: records[5][1].__setitem__("extra_runtime_permission_approved", True),
            "approved permission set mismatch",
        ),
        (
            lambda records: records[5][1]["prohibited_scope"].remove("http_header_parsing"),
            "prohibited_scope mismatch",
        ),
        (
            lambda records: records[5][1].__setitem__("identity_verification_enabled", True),
            "identity_verification_enabled must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("authenticated_requests_enabled", True),
            "authenticated_requests_enabled must be false",
        ),
        (
            lambda records: records[5][1].__setitem__(
                "authorization_header_parsing_approved",
                True,
            ),
            "authorization_header_parsing_approved must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("cookie_parsing_approved", True),
            "cookie_parsing_approved must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("credential_verification_approved", True),
            "credential_verification_approved must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("external_identity_provider_approved", True),
            "external_identity_provider_approved must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("login_endpoint_approved", True),
            "login_endpoint_approved must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("openapi_security_scheme_added", True),
            "openapi_security_scheme_added must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("package_files_added", True),
            "package_files_added must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("migrations_added", True),
            "migrations_added must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("v02_tag_created", True),
            "v02_tag_created must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("v02_release_created", True),
            "v02_release_created must be false",
        ),
    ],
)
def test_aion157_validator_rejects_bad_lifecycle(mutator: Any, match: str) -> None:
    records = _canonical_records()
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_aion157_does_not_change_protected_sources_or_add_release_artifacts() -> None:
    changed = _changed_files() - AION160_ALLOWED_CHANGED_PATHS - AION162_ALLOWED_CHANGED_PATHS
    for forbidden in PROTECTED_SOURCE_PATHS:
        assert not any(path == forbidden or path.startswith(f"{forbidden}/") for path in changed)
    assert not any(path.endswith("package.json") for path in changed)
    assert not any(path.endswith("package-lock.json") for path in changed)
    assert not any(path.endswith("pnpm-lock.yaml") for path in changed)
    assert not any(path.endswith("yarn.lock") for path in changed)
    assert not any(path.endswith("bun.lockb") for path in changed)
    assert not any("migration" in Path(path).name.lower() for path in changed)
    assert not any(path.startswith("migrations/") for path in changed)


def test_aion157_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-157 focused script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def test_aion157_does_not_create_v02_release_or_tag() -> None:
    tags = subprocess.run(
        ["git", "tag", "--list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert not {"v0.2", "v0.2.0", "aion-v0.2", "aion-v0.2.0"} & set(tags)

    for release in ("v0.2", "aion-v0.2"):
        result = subprocess.run(
            ["gh", "release", "view", release],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        assert result.returncode != 0


def _canonical_records() -> list[tuple[str, dict[str, Any]]]:
    return [
        ("aion151.json", _payload_from_spec(AION151_AUTHORIZATION)),
        ("aion153.json", _payload_from_spec(AION153_AUTHORIZATION)),
        ("aion155.json", _payload_from_spec(AION155_AUTHORIZATION)),
        ("aion157.json", _payload_from_spec(AION157_AUTHORIZATION)),
        ("aion159.json", _payload_from_spec(AION159_AUTHORIZATION)),
        ("aion161.json", _payload_from_spec(AION161_AUTHORIZATION)),
    ]


def _payload_from_spec(spec: Any) -> dict[str, Any]:
    payload = {
        "task_id": spec.task_id,
        "record_kind": "unit_test_authorization_record",
        "artifact": "unit-test",
        "synthetic": True,
        "read_only": True,
        "authorization_transaction_id": spec.transaction_id,
        "approval_record_id": spec.approval_record_id,
        "parent_authorization_transaction_id": spec.parent_authorization_transaction_id,
        "candidate_id": spec.candidate_id,
        "workstream": spec.workstream,
        "implementation_task": spec.implementation_task,
        "authorization_scope": spec.authorization_scope,
        "authorization_active": spec.authorization_active,
        "authorization_consumed": spec.authorization_consumed,
        "authorization_consumed_by_task": spec.authorization_consumed_by_task,
        "authorization_consumed_by_pr": spec.authorization_consumed_by_pr,
        "authorization_consumed_by_feature_commit": spec.authorization_consumed_by_feature_commit,
        "authorization_consumed_by_merge_commit": spec.authorization_consumed_by_merge_commit,
        "authorization_expired": spec.authorization_expired,
        "authorization_reusable": spec.authorization_reusable,
        "runtime_guard_hold_active": True,
        "runtime_no_go_status": True,
        "approved_scope": sorted(spec.approved_scope),
        "prohibited_scope": sorted(spec.prohibited_scope),
        "required_adr": spec.required_adr,
        "required_gates": ["unit-test-gate"],
        "evidence_references": ["unit-test-evidence"],
        "reviewer_roles": ["security reviewer"],
        "expiry": spec.expiry,
        "revocation_path": "unit test revocation path",
    }
    for key in APPROVAL_TRUE_KEYS:
        payload[key] = True
    for key in spec.false_keys:
        payload[key] = False
    for key in spec.implementation_true_keys:
        payload[key] = True
    if spec.approved_dependency_name is not None:
        payload["approved_dependency"] = {
            "name": spec.approved_dependency_name,
            "specifier": spec.approved_dependency_specifier,
            "manifest": spec.approved_dependency_manifest,
            "change_count": spec.approved_dependency_change_count,
        }
    return copy.deepcopy(payload)


def _unknown_active_payload() -> dict[str, Any]:
    payload = _payload_from_spec(AION161_AUTHORIZATION)
    payload["authorization_transaction_id"] = "AION-999-PA-9999"
    payload["approval_record_id"] = "AION-999-PA-9999"
    return payload


def _changed_files() -> set[str]:
    base = _comparison_base()
    if base is None:
        return set()
    diff = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", base, "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return {
        line.strip()
        for line in [*diff.stdout.splitlines(), *untracked.stdout.splitlines()]
        if line.strip()
    }


def _comparison_base() -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if _git_ref_exists(candidate):
            merge_base = subprocess.run(
                ["git", "merge-base", "HEAD", candidate],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    if _git_ref_exists("HEAD~1"):
        return "HEAD~1"
    return None


def _git_ref_exists(ref: str) -> bool:
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", ref],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        ).returncode
        == 0
    )


def _json(relative: str) -> dict[str, Any]:
    return json.loads((ROOT / relative).read_text())


def _text(relative: str) -> str:
    return (ROOT / relative).read_text()
