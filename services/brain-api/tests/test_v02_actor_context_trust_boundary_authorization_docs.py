"""AION-159 actor-context trust-boundary authorization tests."""

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
    ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS,
    ACTOR_CONTEXT_TRUST_BOUNDARY_PROHIBITED_SCOPE,
    ACTOR_CONTEXT_TRUST_BOUNDARY_TRUE_KEYS,
    AION151_AUTHORIZATION,
    AION153_AUTHORIZATION,
    AION155_AUTHORIZATION,
    AION157_AUTHORIZATION,
    AION159_AUTHORIZATION,
    APPROVAL_TRUE_KEYS,
    REQUEST_IDENTITY_STABILIZATION_TRUE_KEYS,
    validate_authorization_lifecycle_payloads,
)

AION158_FEATURE_COMMIT = "767fd9b228b00b04569df2e3b1b3f6bc9ecd846f"
AION158_MERGE_COMMIT = "f792c92e1d8a73ec8e7377b5d59269dea359006d"

DOCS = [
    "docs/release/v02-request-identity-stabilization-closeout.md",
    "docs/release/v02-actor-context-trust-boundary-authorization-transaction.md",
    "docs/release/v02-actor-context-trust-boundary-explicit-approval-record.md",
    "docs/release/v02-actor-context-trust-boundary-scope.md",
    "docs/release/v02-actor-context-trust-boundary-runtime-hold.md",
    "docs/release/v02-actor-context-trust-boundary-evidence-matrix.md",
    "docs/release/v02-actor-context-trust-boundary-no-go.md",
    "docs/release/v02-actor-context-trust-boundary-checklist.md",
    "docs/adr/0150-v02-actor-context-trust-boundary-authorization.md",
]

JSON_ARTIFACTS = [
    "examples/release/v02-request-identity-stabilization-closeout.json",
    "examples/release/v02-actor-context-trust-boundary-authorization.json",
    "examples/release/v02-actor-context-trust-boundary-explicit-approval-record.json",
    "examples/release/v02-actor-context-trust-boundary-runtime-hold.json",
    "examples/release/v02-actor-context-trust-boundary-evidence-matrix.json",
    "operator-console-static/demo-data/v02-actor-context-trust-boundary-authorization.json",
]

AION159_JSON_ARTIFACTS = JSON_ARTIFACTS[1:]

SCRIPTS = [
    "scripts/v02-actor-context-trust-boundary-authorization-no-go-regression.sh",
    "scripts/v02-actor-context-trust-boundary-authorization-check.sh",
]

PROTECTED_SOURCE_PATHS = [
    "services/brain-api/src/aion_brain/identity/dev_auth.py",
    "services/brain-api/src/aion_brain/contracts/scopes.py",
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/production_auth",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel",
    "services/brain-api/src/aion_brain/api_support",
    "services/brain-api/src/aion_brain/api",
    "packages/aion-sdk-python/src",
]

AION160_REMEDIATION_PATHS = {
    "services/brain-api/src/aion_brain/contracts/actor_context_resolution.py",
    "services/brain-api/src/aion_brain/identity/dev_auth.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/actor_context.py",
    "services/brain-api/src/aion_brain/production_auth/actor_context_evidence.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
}


def test_aion159_required_files_exist_and_status_is_current() -> None:
    for relative in DOCS + JSON_ARTIFACTS + SCRIPTS:
        assert (ROOT / relative).exists(), relative
    assert "0150-v02-actor-context-trust-boundary-authorization.md" in _text(
        "docs/adr/README.md"
    )

    status = _text("docs/project-status.md")
    assert (
        "Current milestone: AION-158 request-identity stabilization merged." in status
        or "Current milestone: AION-160 actor-context trust-boundary remediation implemented."
        in status
    )
    assert (
        "Current authorization: AION-159-PA-0005 active for AION-160." in status
        or "Current authorization: AION-159-PA-0005 consumed by AION-160 when merged."
        in status
    )
    assert (
        "Next task: AION-160 actor-context trust-boundary remediation." in status
        or "Formal lifecycle closeout: AION-161." in status
    )

    readiness = _text("docs/release/v02-release-readiness-delta.md")
    assert "Request identity stabilization" in readiness
    assert "Actor-context trust-boundary remediation" in readiness
    assert (
        "`AION-160` is the next critical path" in readiness
        or "AION-160 remediates the actor-context trust boundary" in readiness
    )
    assert "`v02_release_ready=false`" in readiness
    assert "`v02_tag_created=false`" in readiness
    assert "`v02_release_created=false`" in readiness


def test_aion159_json_is_valid_synthetic_read_only_and_exactly_scoped() -> None:
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True

    closeout = _json("examples/release/v02-request-identity-stabilization-closeout.json")
    assert closeout["task_id"] == "AION-159"
    assert closeout["record_kind"] == "request_identity_stabilization_closeout"
    assert closeout["authorization_transaction_id"] == "AION-157-PA-0004"
    assert closeout["authorization_active"] is False
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_consumed_by_task"] == "AION-158"
    assert closeout["authorization_consumed_by_pr"] == 68
    assert closeout["authorization_consumed_by_feature_commit"] == AION158_FEATURE_COMMIT
    assert closeout["authorization_consumed_by_merge_commit"] == AION158_MERGE_COMMIT
    assert closeout["authorization_expired"] is True
    assert closeout["authorization_reusable"] is False
    assert closeout["request_identity_middleware_implementation"] == "pure_asgi"
    assert closeout["request_identity_boundary_state"] == "implemented_disabled"
    assert closeout["identity_verification_enabled"] is False
    assert closeout["authenticated_requests_enabled"] is False
    assert closeout["production_auth_runtime_enabled"] is False

    for relative in AION159_JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-159"
        assert payload["authorization_transaction_id"] == "AION-159-PA-0005"
        assert payload["approval_record_id"] == "AION-159-PA-0005"
        assert payload["parent_authorization_transaction_id"] == "AION-157-PA-0004"
        assert payload["candidate_id"] == "production-auth-actor-context-trust-boundary"
        assert payload["workstream"] == "production-auth-route-context-hardening"
        assert payload["implementation_task"] == "AION-160"
        assert payload["authorization_scope"] == "fail-closed-actor-context-resolution"
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS | ACTOR_CONTEXT_TRUST_BOUNDARY_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in ACTOR_CONTEXT_TRUST_BOUNDARY_FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert set(payload["approved_scope"]) == AION159_AUTHORIZATION.approved_scope
        assert set(payload["prohibited_scope"]) == ACTOR_CONTEXT_TRUST_BOUNDARY_PROHIBITED_SCOPE
        assert payload["required_adr"] == AION159_AUTHORIZATION.required_adr
        assert payload["expiry"] == AION159_AUTHORIZATION.expiry


def test_aion157_is_historical_and_aion159_is_only_active_record() -> None:
    validate_authorization_lifecycle_payloads(_canonical_records())
    aion157 = _payload_from_spec(AION157_AUTHORIZATION)
    assert aion157["authorization_active"] is False
    assert aion157["authorization_consumed"] is True
    assert aion157["authorization_consumed_by_task"] == "AION-158"
    assert aion157["authorization_consumed_by_pr"] == 68
    assert aion157["authorization_consumed_by_feature_commit"] == AION158_FEATURE_COMMIT
    assert aion157["authorization_consumed_by_merge_commit"] == AION158_MERGE_COMMIT
    assert aion157["authorization_expired"] is True
    assert aion157["authorization_reusable"] is False
    for key in APPROVAL_TRUE_KEYS | REQUEST_IDENTITY_STABILIZATION_TRUE_KEYS:
        assert aion157[key] is True


def test_aion159_trust_boundary_finding_is_documented_from_source() -> None:
    source = _text("services/brain-api/src/aion_brain/identity/dev_auth.py")
    docs = _text("docs/release/v02-actor-context-trust-boundary-authorization-transaction.md")
    remediated = _text("docs/release/v02-actor-context-trust-boundary-remediation.md")
    assert (
        'dev_enabled = settings.env == "development" and settings.dev_auth_enabled'
        in source
        or 'return settings.env == "development" and settings.dev_auth_enabled is True'
        in source
    )
    for header in (
        "X-AION-Actor-ID",
        "X-AION-Workspace-ID",
        "X-AION-Roles",
        "X-AION-Permissions",
        "X-AION-Security-Scope",
    ):
        assert header in source
        assert header in docs
    assert "non-development identity-header trust fallback" in docs
    assert (
        "AION-159 changes no implementation source" in docs
        or "AION-160 remediates that behavior" in remediated
    )


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records.append(
                (
                    "duplicate-active.json",
                    _payload_from_spec(AION157_AUTHORIZATION) | {"authorization_active": True},
                )
            ),
            "authorization_active must be false",
        ),
        (
            lambda records: records.append(("unknown.json", _unknown_active_payload())),
            "unknown approved authorization record",
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
            lambda records: records[4][1].__setitem__("authorization_consumed", True),
            "authorization_consumed must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("authorization_expired", True),
            "authorization_expired must be false",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "parent_authorization_transaction_id",
                "AION-155-PA-0003",
            ),
            "parent_authorization_transaction_id mismatch",
        ),
        (
            lambda records: records[4][1].__setitem__("implementation_task", "AION-159"),
            "implementation_task mismatch",
        ),
        (
            lambda records: records[4][1].__setitem__("candidate_id", "production-auth-runtime"),
            "candidate_id mismatch",
        ),
        (
            lambda records: records[4][1].__setitem__("workstream", "production-auth-runtime"),
            "workstream mismatch",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "authorization_scope",
                "fail-closed-actor-context-resolution-and-login",
            ),
            "authorization_scope mismatch",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "actor_context_trust_boundary_remediation_approved",
                False,
            ),
            "actor_context_trust_boundary_remediation_approved must be true",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "extra_actor_context_permission_approved",
                True,
            ),
            "approved permission set mismatch",
        ),
        (
            lambda records: records[4][1]["prohibited_scope"].remove(
                "production_identity_header_trust"
            ),
            "prohibited_scope mismatch",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "production_identity_header_trust_approved",
                True,
            ),
            "production_identity_header_trust_approved must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("production_role_header_trust_enabled", True),
            "production_role_header_trust_enabled must be false",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "production_permission_header_trust_enabled",
                True,
            ),
            "production_permission_header_trust_enabled must be false",
        ),
        (
            lambda records: records[4][1].__setitem__(
                "production_security_scope_header_trust_enabled",
                True,
            ),
            "production_security_scope_header_trust_enabled must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("identity_verification_enabled", True),
            "identity_verification_enabled must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("authenticated_requests_enabled", True),
            "authenticated_requests_enabled must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("protected_material_handling_approved", True),
            "protected_material_handling_approved must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("provider_sdk_approved", True),
            "provider_sdk_approved must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("package_files_added", True),
            "package_files_added must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("migrations_added", True),
            "migrations_added must be false",
        ),
        (
            lambda records: records[4][1].__setitem__("v02_release_created", True),
            "v02_release_created must be false",
        ),
    ],
)
def test_aion159_validator_rejects_bad_lifecycle(mutator: Any, match: str) -> None:
    records = _canonical_records()
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_aion159_does_not_change_protected_sources_or_add_release_artifacts() -> None:
    changed = _changed_files()
    for forbidden in PROTECTED_SOURCE_PATHS:
        assert not any(
            (path == forbidden or path.startswith(f"{forbidden}/"))
            and path not in AION160_REMEDIATION_PATHS
            for path in changed
        )
    assert not any(path.endswith("package.json") for path in changed)
    assert not any(path.endswith("package-lock.json") for path in changed)
    assert not any(path.endswith("pnpm-lock.yaml") for path in changed)
    assert not any(path.endswith("yarn.lock") for path in changed)
    assert not any(path.endswith("bun.lockb") for path in changed)
    assert not any("migration" in Path(path).name.lower() for path in changed)
    assert not any(path.startswith("migrations/") for path in changed)


def test_aion159_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-159 focused script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def test_aion159_does_not_create_v02_release_or_tag() -> None:
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
    return copy.deepcopy(payload)


def _unknown_active_payload() -> dict[str, Any]:
    payload = _payload_from_spec(AION159_AUTHORIZATION)
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
