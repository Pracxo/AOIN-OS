"""AION-153 production-auth stabilization authorization tests."""

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
    AION163_AUTHORIZATION,
    APPROVAL_TRUE_KEYS,
    validate_authorization_lifecycle_payloads,
)

DOCS = [
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

JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-stabilization-authorization.json",
    "examples/release/v02-production-auth-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json",
]

SCRIPTS = [
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-stabilization-runtime-guard-hold.sh",
    "scripts/v02-production-auth-stabilization-authorization-no-go-regression.sh",
]

FORBIDDEN_CHANGED_PATHS = [
    "services/brain-api/src/aion_brain/production_auth",
    "services/brain-api/src/aion_brain/contracts/production_auth.py",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
    "services/brain-api/src/aion_brain/api",
    "packages/aion-sdk-python/src",
    "migrations",
]

AION156_ALLOWED_CHANGED_PATHS = {
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/request_boundary.py",
    "services/brain-api/src/aion_brain/production_auth/request_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/request_middleware.py",
    "services/brain-api/src/aion_brain/production_auth/verifier.py",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel/app_factory.py",
    "services/brain-api/src/aion_brain/kernel/container.py",
    "services/brain-api/src/aion_brain/kernel/diagnostics.py",
}

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


def test_v02_production_auth_stabilization_docs_exist_and_show_consumed_state() -> None:
    for relative in DOCS:
        assert (ROOT / relative).exists(), relative
    assert "0144-v02-production-auth-core-stabilization-authorization.md" in _text(
        "docs/adr/README.md"
    )

    transaction = _text(
        "docs/release/v02-production-auth-stabilization-authorization-transaction.md"
    )
    for required in [
        "authorization_transaction_id=AION-153-PA-0002",
        "approval_record_id=AION-153-PA-0002",
        "parent_authorization_transaction_id=AION-151-PA-0001",
        "candidate_id=production-auth-core-stabilization",
        "workstream=production-auth-hardening",
        "implementation_task=AION-154",
        "authorization_scope=disabled-production-auth-core-stabilization",
        "authorization_active=false",
        "authorization_consumed=true",
        "authorization_consumed_by_pr=64",
        "authorization_consumed_by_feature_commit=f001632ed0566bcf7facfe8905a2781ff9fa6ce9",
        "authorization_consumed_by_merge_commit=85584ea1976fd6f2cb73a641464b3caf87481618",
        "authorization_expired=true",
        "authorization_reusable=false",
    ]:
        assert required in transaction


def test_v02_production_auth_stabilization_json_is_historical() -> None:
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-153"
        assert payload["synthetic"] is True
        assert payload["read_only"] is True
        assert payload["authorization_transaction_id"] == "AION-153-PA-0002"
        assert payload["approval_record_id"] == "AION-153-PA-0002"
        assert payload["parent_authorization_transaction_id"] == "AION-151-PA-0001"
        assert payload["candidate_id"] == "production-auth-core-stabilization"
        assert payload["workstream"] == "production-auth-hardening"
        assert payload["implementation_task"] == "AION-154"
        assert payload["authorization_scope"] == "disabled-production-auth-core-stabilization"
        assert payload["authorization_active"] is False
        assert payload["authorization_consumed"] is True
        assert payload["authorization_consumed_by_task"] == "AION-154"
        assert payload["authorization_consumed_by_pr"] == 64
        assert (
            payload["authorization_consumed_by_feature_commit"]
            == "f001632ed0566bcf7facfe8905a2781ff9fa6ce9"
        )
        assert (
            payload["authorization_consumed_by_merge_commit"]
            == "85584ea1976fd6f2cb73a641464b3caf87481618"
        )
        assert payload["authorization_expired"] is True
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in AION153_AUTHORIZATION.false_keys:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert set(payload["approved_scope"]) == AION153_AUTHORIZATION.approved_scope
        assert set(payload["prohibited_scope"]) == AION153_AUTHORIZATION.prohibited_scope
        assert payload["required_adr"] == AION153_AUTHORIZATION.required_adr
        assert payload["expiry"] == AION153_AUTHORIZATION.expiry


def test_v02_production_auth_stabilization_validator_accepts_current_lifecycle() -> None:
    validate_authorization_lifecycle_payloads(
        [
            ("aion151.json", _payload_from_spec(AION151_AUTHORIZATION)),
            ("aion153.json", _payload_from_spec(AION153_AUTHORIZATION)),
            ("aion155.json", _payload_from_spec(AION155_AUTHORIZATION)),
            ("aion157.json", _payload_from_spec(AION157_AUTHORIZATION)),
            ("aion159.json", _payload_from_spec(AION159_AUTHORIZATION)),
            ("aion163.json", _payload_from_spec(AION163_AUTHORIZATION)),
            ("aion161.json", _payload_from_spec(AION161_AUTHORIZATION)),
        ]
    )


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records[1][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[1][1].__setitem__("authorization_reusable", True),
            "authorization_reusable must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("authorization_consumed", True),
            "authorization_consumed must be false",
        ),
        (
            lambda records: records[3][1].__setitem__(
                "authorization_scope",
                "disabled-request-identity-boundary-stabilization-and-login",
            ),
            "authorization_scope mismatch",
        ),
    ],
)
def test_v02_production_auth_stabilization_validator_rejects_bad_lifecycle(
    mutator: Any,
    match: str,
) -> None:
    records = [
        ("aion151.json", _payload_from_spec(AION151_AUTHORIZATION)),
        ("aion153.json", _payload_from_spec(AION153_AUTHORIZATION)),
        ("aion155.json", _payload_from_spec(AION155_AUTHORIZATION)),
        ("aion157.json", _payload_from_spec(AION157_AUTHORIZATION)),
        ("aion159.json", _payload_from_spec(AION159_AUTHORIZATION)),
        ("aion163.json", _payload_from_spec(AION163_AUTHORIZATION)),
        ("aion161.json", _payload_from_spec(AION161_AUTHORIZATION)),
    ]
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_v02_production_auth_stabilization_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["AION_V02_PRODUCTION_AUTH_STABILIZATION_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_PRODUCTION_AUTH_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK"] = "1"
    env["AION_PRODUCTION_AUTH_CORE_RUNTIME_HOLD_SKIP_FULL_CHECK"] = "1"
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-153 focused script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def test_v02_production_auth_stabilization_does_not_change_forbidden_sources() -> None:
    changed = (
        _changed_files()
        - AION156_ALLOWED_CHANGED_PATHS
        - AION160_ALLOWED_CHANGED_PATHS
        - AION162_ALLOWED_CHANGED_PATHS
    )
    for forbidden in FORBIDDEN_CHANGED_PATHS:
        assert not any(path == forbidden or path.startswith(f"{forbidden}/") for path in changed)
    assert not any(path.endswith("package.json") for path in changed)
    assert not any(path.endswith("package-lock.json") for path in changed)
    assert not any(path.endswith("pnpm-lock.yaml") for path in changed)
    assert not any(path.endswith("yarn.lock") for path in changed)
    assert not any(path.endswith("bun.lockb") for path in changed)
    assert not any("migration" in Path(path).name.lower() for path in changed)
    assert not any(path.startswith("services/brain-api/src/aion_brain/api/") for path in changed)


def test_v02_production_auth_stabilization_does_not_create_v02_release_or_tag() -> None:
    tags = subprocess.run(
        ["git", "tag", "--list"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.splitlines()
    assert not {"v0.2", "v0.2.0", "aion-v0.2", "aion-v0.2.0"} & set(tags)


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
