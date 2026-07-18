"""AION-161 offline identity assertion verification authorization tests."""

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
    AION_162_CORRECTIVE_FEATURE_COMMIT,
    AION_162_CORRECTIVE_MERGE_COMMIT,
    AION_162_FINAL_MAIN_COMMIT,
    AION_162_PRIMARY_FEATURE_COMMIT,
    AION_162_PRIMARY_MERGE_COMMIT,
    APPROVAL_TRUE_KEYS,
    OFFLINE_IDENTITY_ASSERTION_APPROVED_SCOPE,
    OFFLINE_IDENTITY_ASSERTION_FALSE_KEYS,
    OFFLINE_IDENTITY_ASSERTION_PROHIBITED_SCOPE,
    OFFLINE_IDENTITY_ASSERTION_TRUE_KEYS,
    validate_authorization_lifecycle_payloads,
)

AION160_FEATURE_COMMIT = "085b1b9d9cbbc23a735c1a82be66a2e901a56761"
AION160_MERGE_COMMIT = "bfc2afdc96358559027ee36efc0bc26ed3bb796d"

DOCS = [
    "docs/release/v02-actor-context-trust-boundary-remediation-closeout.md",
    "docs/release/v02-offline-identity-assertion-verification-authorization-transaction.md",
    "docs/release/v02-offline-identity-assertion-verification-explicit-approval-record.md",
    "docs/release/v02-offline-identity-assertion-verification-scope.md",
    "docs/release/v02-offline-identity-assertion-verification-threat-model.md",
    "docs/release/v02-offline-identity-assertion-verification-runtime-hold.md",
    "docs/release/v02-offline-identity-assertion-verification-evidence-matrix.md",
    "docs/release/v02-offline-identity-assertion-verification-no-go.md",
    "docs/release/v02-offline-identity-assertion-verification-checklist.md",
    "docs/adr/0152-v02-offline-ed25519-identity-assertion-verification-authorization.md",
]

JSON_ARTIFACTS = [
    "examples/release/v02-actor-context-trust-boundary-remediation-closeout.json",
    "examples/release/v02-offline-identity-assertion-verification-authorization.json",
    "examples/release/v02-offline-identity-assertion-verification-explicit-approval-record.json",
    "examples/release/v02-offline-identity-assertion-verification-runtime-hold.json",
    "examples/release/v02-offline-identity-assertion-verification-evidence-matrix.json",
    "operator-console-static/demo-data/v02-offline-identity-assertion-verification-authorization.json",
]

AION161_JSON_ARTIFACTS = JSON_ARTIFACTS[1:]

SCRIPTS = [
    "scripts/v02-offline-identity-assertion-verification-authorization-no-go-regression.sh",
    "scripts/v02-offline-identity-assertion-verification-authorization-check.sh",
]

PROTECTED_SOURCE_PATHS = [
    "services/brain-api/src/aion_brain/contracts/actor_context_resolution.py",
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/identity/dev_auth.py",
    "services/brain-api/src/aion_brain/production_auth",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel",
    "services/brain-api/src/aion_brain/api_support",
    "services/brain-api/src/aion_brain/api",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
]

AION162_ALLOWED_CHANGED_PATHS = {
    "services/brain-api/pyproject.toml",
    "services/brain-api/src/aion_brain/contracts/identity_assertion.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_verifier.py",
    "services/brain-api/src/aion_brain/production_auth/trusted_public_keys.py",
}


def test_aion161_required_files_exist_and_status_is_current() -> None:
    for relative in DOCS + JSON_ARTIFACTS + SCRIPTS:
        assert (ROOT / relative).exists(), relative
    assert "0152-v02-offline-ed25519-identity-assertion-verification-authorization.md" in _text(
        "docs/adr/README.md"
    )

    status = _text("docs/project-status.md")
    assert (
        "Current authorization: AION-161-PA-0006 active for AION-162." in status
        or "Current authorization: AION-161-PA-0006 consumed by AION-162 when merged." in status
        or "AION-161-PA-0006 consumed by AION-162 when merged." in status
    )
    assert "AION-162 offline Ed25519 identity assertion verification core" in status
    assert "Production authentication runtime remains disabled." in status

    ledger = _text("docs/release/v02-explicit-approval-record-master-ledger.md")
    assert "AION-159-PA-0005" in ledger
    assert "AION-161-PA-0006" in ledger


def test_aion160_closeout_json_is_consumed_and_non_reusable() -> None:
    payload = _json("examples/release/v02-actor-context-trust-boundary-remediation-closeout.json")
    assert payload["task_id"] == "AION-161"
    assert payload["record_kind"] == "actor_context_trust_boundary_remediation_closeout"
    assert payload["authorization_transaction_id"] == "AION-159-PA-0005"
    assert payload["authorization_active"] is False
    assert payload["authorization_consumed"] is True
    assert payload["authorization_consumed_by_task"] == "AION-160"
    assert payload["authorization_consumed_by_pr"] == 70
    assert payload["authorization_consumed_by_feature_commit"] == AION160_FEATURE_COMMIT
    assert payload["authorization_consumed_by_merge_commit"] == AION160_MERGE_COMMIT
    assert payload["authorization_expired"] is True
    assert payload["authorization_reusable"] is False
    assert payload["actor_context_trust_boundary_remediated"] is True
    assert payload["actor_context_resolution_state"] == "implemented_fail_closed"
    assert payload["non_development_identity_headers_ignored"] is True
    assert payload["authenticated_actor_context_enabled"] is False
    assert payload["production_auth_runtime_enabled"] is False


def test_aion161_json_is_valid_synthetic_read_only_and_exactly_scoped() -> None:
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True

    for relative in AION161_JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-161"
        assert payload["authorization_transaction_id"] == "AION-161-PA-0006"
        assert payload["approval_record_id"] == "AION-161-PA-0006"
        assert payload["parent_authorization_transaction_id"] == "AION-159-PA-0005"
        assert payload["candidate_id"] == "production-auth-offline-identity-assertion-verification"
        assert payload["workstream"] == "production-auth-verification-core"
        assert payload["implementation_task"] == "AION-162"
        assert payload["authorization_scope"] == "offline-ed25519-identity-assertion-verification"
        assert payload["authorization_active"] is False
        assert payload["authorization_consumed"] is True
        assert payload["authorization_expired"] is True
        assert payload["authorization_reusable"] is False
        assert payload["authorization_consumed_by_task"] == "AION-162"
        assert payload["authorization_consumed_by_primary_pr"] == 72
        assert (
            payload["authorization_consumed_by_primary_feature_commit"]
            == AION_162_PRIMARY_FEATURE_COMMIT
        )
        assert (
            payload["authorization_consumed_by_primary_merge_commit"]
            == AION_162_PRIMARY_MERGE_COMMIT
        )
        assert payload["authorization_post_merge_correction_pr"] == 73
        assert (
            payload["authorization_post_merge_correction_feature_commit"]
            == AION_162_CORRECTIVE_FEATURE_COMMIT
        )
        assert (
            payload["authorization_post_merge_correction_merge_commit"]
            == AION_162_CORRECTIVE_MERGE_COMMIT
        )
        assert payload["authorization_final_verified_main_commit"] == AION_162_FINAL_MAIN_COMMIT
        assert payload["signature_algorithm"] == "Ed25519"
        assert payload["algorithm_negotiation_approved"] is False
        assert payload["signature_domain"] == "AION-IDENTITY-ASSERTION-V1"
        assert payload["approved_dependency"] == {
            "name": "cryptography",
            "specifier": ">=49.0.0,<50.0.0",
            "manifest": "services/brain-api/pyproject.toml",
            "change_count": 1,
        }
        for key in APPROVAL_TRUE_KEYS | OFFLINE_IDENTITY_ASSERTION_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in OFFLINE_IDENTITY_ASSERTION_FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert payload["cryptographic_verification_result_may_be_true"] is True
        assert payload["request_authentication_result_must_remain_false"] is True
        assert payload["replay_protection_required_before_request_integration"] is True
        result = payload["verification_result_contract"]
        assert result["verified_may_be_true"] is True
        assert result["request_authenticated"] is False
        assert result["actor_context_applied"] is False
        assert result["request_identity_context_applied"] is False
        assert result["runtime_effect"] is False
        assert result["replay_check_performed"] is False
        assert set(payload["approved_scope"]) == OFFLINE_IDENTITY_ASSERTION_APPROVED_SCOPE
        assert set(payload["prohibited_scope"]) == OFFLINE_IDENTITY_ASSERTION_PROHIBITED_SCOPE
        assert payload["required_adr"] == AION161_AUTHORIZATION.required_adr
        assert payload["expiry"] == AION161_AUTHORIZATION.expiry


def test_aion161_is_only_active_authorization_record() -> None:
    validate_authorization_lifecycle_payloads(_canonical_records())
    aion159 = _payload_from_spec(AION159_AUTHORIZATION)
    assert aion159["authorization_active"] is False
    assert aion159["authorization_consumed"] is True
    assert aion159["authorization_consumed_by_task"] == "AION-160"
    assert aion159["authorization_consumed_by_pr"] == 70
    assert aion159["authorization_consumed_by_feature_commit"] == AION160_FEATURE_COMMIT
    assert aion159["authorization_consumed_by_merge_commit"] == AION160_MERGE_COMMIT
    assert aion159["authorization_expired"] is True
    assert aion159["authorization_reusable"] is False

    aion161 = _payload_from_spec(AION161_AUTHORIZATION)
    assert aion161["authorization_active"] is False
    assert aion161["authorization_consumed"] is True
    assert aion161["authorization_consumed_by_task"] == "AION-162"
    assert aion161["authorization_expired"] is True
    assert aion161["authorization_reusable"] is False

    aion163 = _payload_from_spec(AION163_AUTHORIZATION)
    assert aion163["authorization_active"] is True
    assert aion163["authorization_consumed"] is False
    assert aion163["authorization_expired"] is False
    assert aion163["authorization_reusable"] is False


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records[4][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records.append(("unknown.json", _unknown_active_payload())),
            "unknown approved authorization record",
        ),
        (
            lambda records: records[6][1].__setitem__("authorization_consumed", True),
            "authorization_consumed must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("authorization_expired", True),
            "authorization_expired must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("authorization_reusable", True),
            "authorization_reusable must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "parent_authorization_transaction_id",
                "AION-157-PA-0004",
            ),
            "parent_authorization_transaction_id mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("implementation_task", "AION-161"),
            "implementation_task mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("candidate_id", "production-auth-runtime"),
            "candidate_id mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "authorization_scope",
                "offline-ed25519-identity-assertion-verification-and-request-auth",
            ),
            "authorization_scope mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "atomic_replay_claim_approved",
                False,
            ),
            "atomic_replay_claim_approved must be true",
        ),
        (
            lambda records: records[6][1].__setitem__("extra_crypto_permission_approved", True),
            "approved permission set mismatch",
        ),
        (
            lambda records: records[6][1]["approved_scope"].remove("atomic_replay_claim"),
            "approved_scope mismatch",
        ),
        (
            lambda records: records[6][1]["prohibited_scope"].remove("runtime_private_key"),
            "prohibited_scope mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("dependency_change_approved", True),
            "dependency_change_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("database_migration_approved", True),
            "database_migration_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "identity_assertion_header_parsing_approved",
                True,
            ),
            "identity_assertion_header_parsing_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "runtime_private_key_material_approved",
                True,
            ),
            "runtime_private_key_material_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("jwks_network_fetch_approved", True),
            "jwks_network_fetch_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("replay_cache_approved", True),
            "replay_cache_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("runtime_effect", True),
            "runtime_effect must be false",
        ),
    ],
)
def test_aion161_validator_rejects_bad_lifecycle(mutator: Any, match: str) -> None:
    records = _canonical_records()
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_aion161_does_not_change_protected_sources_or_add_release_artifacts() -> None:
    changed = _changed_files() - AION162_ALLOWED_CHANGED_PATHS
    for forbidden in PROTECTED_SOURCE_PATHS:
        assert not any(path == forbidden or path.startswith(f"{forbidden}/") for path in changed)
    assert not any(path.endswith("package.json") for path in changed)
    assert not any(path.endswith("package-lock.json") for path in changed)
    assert not any(path.endswith("pnpm-lock.yaml") for path in changed)
    assert not any(path.endswith("yarn.lock") for path in changed)
    assert not any(path.endswith("bun.lockb") for path in changed)
    assert not any("migration" in Path(path).name.lower() for path in changed)
    assert not any(path.startswith("migrations/") for path in changed)


def test_aion161_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-161 focused script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def test_aion161_does_not_create_v02_release_or_tag() -> None:
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
        ("aion163.json", _payload_from_spec(AION163_AUTHORIZATION)),
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

    if spec.transaction_id == "AION-161-PA-0006":
        payload.update(
            {
                "authorization_consumed_by_primary_pr": 72,
                "authorization_consumed_by_primary_feature_commit": AION_162_PRIMARY_FEATURE_COMMIT,
                "authorization_consumed_by_primary_merge_commit": AION_162_PRIMARY_MERGE_COMMIT,
                "authorization_post_merge_correction_pr": 73,
                "authorization_post_merge_correction_feature_commit": (
                    AION_162_CORRECTIVE_FEATURE_COMMIT
                ),
                "authorization_post_merge_correction_merge_commit": (
                    AION_162_CORRECTIVE_MERGE_COMMIT
                ),
                "authorization_final_verified_main_commit": AION_162_FINAL_MAIN_COMMIT,
            }
        )
    if spec.approved_dependency_name is not None:
        payload["approved_dependency"] = {
            "name": spec.approved_dependency_name,
            "specifier": spec.approved_dependency_specifier,
            "manifest": spec.approved_dependency_manifest,
            "change_count": spec.approved_dependency_change_count,
        }
    return copy.deepcopy(payload)


def _unknown_active_payload() -> dict[str, Any]:
    payload = _payload_from_spec(AION163_AUTHORIZATION)
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
