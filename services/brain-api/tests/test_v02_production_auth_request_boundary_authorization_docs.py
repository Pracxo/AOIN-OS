"""AION-155 production-auth request boundary authorization tests."""

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
    APPROVAL_TRUE_KEYS,
    REQUEST_BOUNDARY_FALSE_KEYS,
    REQUEST_BOUNDARY_IMPLEMENTATION_TRUE_KEYS,
    REQUEST_BOUNDARY_PROHIBITED_SCOPE,
    validate_authorization_lifecycle_payloads,
)

DOCS = [
    "docs/project-status.md",
    "docs/release/v02-production-auth-core-stabilization-closeout.md",
    "docs/release/v02-production-auth-request-boundary-authorization-transaction.md",
    "docs/release/v02-production-auth-request-boundary-scope.md",
    "docs/release/v02-production-auth-request-boundary-runtime-hold.md",
    "docs/release/v02-production-auth-request-boundary-authorization-checklist.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/adr/0146-v02-production-auth-request-boundary-authorization.md",
]

JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-core-stabilization-closeout.json",
    "examples/release/v02-production-auth-request-boundary-authorization.json",
    "examples/release/v02-production-auth-request-boundary-runtime-hold.json",
    "operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json",
]

ACTIVE_JSON_ARTIFACTS = [
    "examples/release/v02-production-auth-request-boundary-authorization.json",
    "examples/release/v02-production-auth-request-boundary-runtime-hold.json",
    "operator-console-static/demo-data/v02-production-auth-request-boundary-authorization.json",
]

SCRIPTS = [
    "scripts/v02-production-auth-request-boundary-authorization-check.sh",
    "scripts/v02-production-auth-request-boundary-authorization-no-go-regression.sh",
]

FORBIDDEN_CHANGED_PATHS = [
    "services/brain-api/src/aion_brain/production_auth",
    "services/brain-api/src/aion_brain/contracts/production_auth.py",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel",
    "services/brain-api/src/aion_brain/api",
    "packages/aion-sdk-python/src",
    "migrations",
]


def test_aion155_required_files_exist_and_readme_state_is_current() -> None:
    for relative in DOCS + JSON_ARTIFACTS:
        assert (ROOT / relative).exists(), relative
    assert "0146-v02-production-auth-request-boundary-authorization.md" in _text(
        "docs/adr/README.md"
    )
    readme = _text("README.md")
    assert "Current Project State" in readme
    assert "currently contains only the AION Brain v0.1 scaffold" not in readme
    assert "stabilized internal disabled production-auth core" in readme.replace("\n", " ")


def test_aion155_json_is_synthetic_read_only_and_exactly_scoped() -> None:
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True

    closeout = _json("examples/release/v02-production-auth-core-stabilization-closeout.json")
    assert closeout["task_id"] == "AION-155"
    assert closeout["record_kind"] == "production_auth_core_stabilization_closeout"
    assert closeout["authorization_transaction_id"] == "AION-153-PA-0002"
    assert closeout["authorization_active"] is False
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_consumed_by_task"] == "AION-154"
    assert closeout["authorization_consumed_by_pr"] == 64
    assert (
        closeout["authorization_consumed_by_feature_commit"]
        == "f001632ed0566bcf7facfe8905a2781ff9fa6ce9"
    )
    assert (
        closeout["authorization_consumed_by_merge_commit"]
        == "85584ea1976fd6f2cb73a641464b3caf87481618"
    )
    assert closeout["authorization_expired"] is True
    assert closeout["authorization_reusable"] is False
    assert closeout["production_auth_core_state"] == "implemented_disabled"
    assert closeout["production_auth_runtime_enabled"] is False
    assert closeout["runtime_no_go_status"] is True

    for relative in ACTIVE_JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-155"
        assert payload["authorization_transaction_id"] == "AION-155-PA-0003"
        assert payload["approval_record_id"] == "AION-155-PA-0003"
        assert payload["parent_authorization_transaction_id"] == "AION-153-PA-0002"
        assert payload["candidate_id"] == "production-auth-request-identity-boundary"
        assert payload["workstream"] == "production-auth-request-integration"
        assert payload["implementation_task"] == "AION-156"
        assert payload["authorization_scope"] == "disabled-request-identity-boundary"
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS | REQUEST_BOUNDARY_IMPLEMENTATION_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in REQUEST_BOUNDARY_FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert set(payload["approved_scope"]) == AION155_AUTHORIZATION.approved_scope
        assert set(payload["prohibited_scope"]) == REQUEST_BOUNDARY_PROHIBITED_SCOPE
        assert payload["required_adr"] == AION155_AUTHORIZATION.required_adr
        assert payload["expiry"] == AION155_AUTHORIZATION.expiry


def test_aion155_validator_accepts_exact_three_record_lifecycle() -> None:
    validate_authorization_lifecycle_payloads(
        [
            ("aion151.json", _payload_from_spec(AION151_AUTHORIZATION)),
            ("aion153.json", _payload_from_spec(AION153_AUTHORIZATION)),
            ("aion155.json", _payload_from_spec(AION155_AUTHORIZATION)),
        ]
    )


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records.append(("duplicate.json", _unknown_active_payload())),
            "unknown approved authorization record",
        ),
        (
            lambda records: records.append(("unknown.json", _unknown_active_payload())),
            "unknown approved authorization record",
        ),
        (
            lambda records: records[1][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[1][1].__setitem__("authorization_reusable", True),
            "authorization_reusable must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("authorization_consumed", True),
            "authorization_consumed must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("authorization_expired", True),
            "authorization_expired must be false",
        ),
        (
            lambda records: records[2][1].__setitem__(
                "parent_authorization_transaction_id",
                "AION-151-PA-0001",
            ),
            "parent_authorization_transaction_id mismatch",
        ),
        (
            lambda records: records[2][1].__setitem__("implementation_task", "AION-155"),
            "implementation_task mismatch",
        ),
        (
            lambda records: records[2][1].__setitem__(
                "authorization_scope",
                "disabled-request-identity-boundary-and-login",
            ),
            "authorization_scope mismatch",
        ),
        (
            lambda records: records[2][1]["approved_scope"].append("login_endpoint"),
            "approved_scope mismatch",
        ),
        (
            lambda records: records[2][1]["prohibited_scope"].remove("token_storage"),
            "prohibited_scope mismatch",
        ),
        (
            lambda records: records[2][1].__setitem__("production_auth_runtime_enabled", True),
            "production_auth_runtime_enabled must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("identity_verification_enabled", True),
            "identity_verification_enabled must be false",
        ),
        (
            lambda records: records[2][1].__setitem__(
                "authorization_header_parsing_approved",
                True,
            ),
            "authorization_header_parsing_approved must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("credential_verification_approved", True),
            "credential_verification_approved must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("token_parsing_approved", True),
            "token_parsing_approved must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("external_identity_provider_approved", True),
            "external_identity_provider_approved must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("package_files_added", True),
            "package_files_added must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("migrations_added", True),
            "migrations_added must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("v02_tag_created", True),
            "v02_tag_created must be false",
        ),
        (
            lambda records: records[2][1].__setitem__("v02_release_created", True),
            "v02_release_created must be false",
        ),
    ],
)
def test_aion155_validator_rejects_bad_lifecycle(mutator: Any, match: str) -> None:
    records = [
        ("aion151.json", _payload_from_spec(AION151_AUTHORIZATION)),
        ("aion153.json", _payload_from_spec(AION153_AUTHORIZATION)),
        ("aion155.json", _payload_from_spec(AION155_AUTHORIZATION)),
    ]
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_aion155_does_not_change_forbidden_sources() -> None:
    changed = _changed_files()
    for forbidden in FORBIDDEN_CHANGED_PATHS:
        assert not any(path == forbidden or path.startswith(f"{forbidden}/") for path in changed)
    assert not any(path.endswith("package.json") for path in changed)
    assert not any(path.endswith("package-lock.json") for path in changed)
    assert not any(path.endswith("pnpm-lock.yaml") for path in changed)
    assert not any(path.endswith("yarn.lock") for path in changed)
    assert not any(path.endswith("bun.lockb") for path in changed)


def test_aion155_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-155 focused script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


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
    payload = _payload_from_spec(AION155_AUTHORIZATION)
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
