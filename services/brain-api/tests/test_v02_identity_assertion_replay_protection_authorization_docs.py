"""AION-163 identity assertion replay protection authorization tests."""

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
    IDENTITY_ASSERTION_REPLAY_PROTECTION_APPROVED_SCOPE,
    IDENTITY_ASSERTION_REPLAY_PROTECTION_FALSE_KEYS,
    IDENTITY_ASSERTION_REPLAY_PROTECTION_PROHIBITED_SCOPE,
    IDENTITY_ASSERTION_REPLAY_PROTECTION_TRUE_KEYS,
    validate_authorization_lifecycle_payloads,
)

DOCS = [
    "docs/release/v02-offline-identity-assertion-verification-closeout.md",
    "docs/release/v02-identity-assertion-replay-protection-authorization-transaction.md",
    "docs/release/v02-identity-assertion-replay-protection-explicit-approval-record.md",
    "docs/release/v02-identity-assertion-replay-protection-scope.md",
    "docs/release/v02-identity-assertion-replay-protection-persistence-model.md",
    "docs/release/v02-identity-assertion-replay-protection-threat-model.md",
    "docs/release/v02-identity-assertion-replay-protection-runtime-hold.md",
    "docs/release/v02-identity-assertion-replay-protection-evidence-matrix.md",
    "docs/release/v02-identity-assertion-replay-protection-no-go.md",
    "docs/release/v02-identity-assertion-replay-protection-checklist.md",
    "docs/adr/0154-v02-identity-assertion-replay-protection-authorization.md",
]

JSON_ARTIFACTS = [
    "examples/release/v02-offline-identity-assertion-verification-closeout.json",
    "examples/release/v02-identity-assertion-replay-protection-authorization.json",
    "examples/release/v02-identity-assertion-replay-protection-explicit-approval-record.json",
    "examples/release/v02-identity-assertion-replay-protection-runtime-hold.json",
    "examples/release/v02-identity-assertion-replay-protection-evidence-matrix.json",
    "operator-console-static/demo-data/v02-identity-assertion-replay-protection-authorization.json",
]

AION163_JSON_ARTIFACTS = JSON_ARTIFACTS[1:]
SCRIPTS = [
    "scripts/v02-identity-assertion-replay-protection-authorization-no-go-regression.sh",
    "scripts/v02-identity-assertion-replay-protection-authorization-check.sh",
]
PROTECTED_SOURCE_PATHS = [
    "services/brain-api/src/aion_brain/contracts/identity_assertion.py",
    "services/brain-api/src/aion_brain/contracts/actor_context_resolution.py",
    "services/brain-api/src/aion_brain/contracts/request_identity.py",
    "services/brain-api/src/aion_brain/production_auth",
    "services/brain-api/src/aion_brain/identity",
    "services/brain-api/src/aion_brain/idempotency",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel",
    "services/brain-api/src/aion_brain/api_support",
    "services/brain-api/src/aion_brain/api",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src",
    "migrations",
]
AION164_IMPLEMENTATION_PATHS = [
    "services/brain-api/src/aion_brain/contracts/identity_assertion_replay.py",
    "services/brain-api/src/aion_brain/production_auth/__init__.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_repository.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_service.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_replay_evidence.py",
    "services/brain-api/src/aion_brain/production_auth/identity_assertion_pipeline.py",
    "services/brain-api/tests/test_identity_assertion_replay_no_dependency_or_migration.py",
]


def test_aion163_required_files_exist_and_json_is_safe() -> None:
    for relative in DOCS + JSON_ARTIFACTS + SCRIPTS:
        assert (ROOT / relative).exists(), relative
    assert "0154-v02-identity-assertion-replay-protection-authorization.md" in _text(
        "docs/adr/README.md"
    )
    for relative in JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True


def test_aion162_closeout_is_exact() -> None:
    payload = _json("examples/release/v02-offline-identity-assertion-verification-closeout.json")
    assert payload["task_id"] == "AION-163"
    assert payload["record_kind"] == "offline_identity_assertion_verification_closeout"
    assert payload["authorization_transaction_id"] == "AION-161-PA-0006"
    assert payload["authorization_active"] is False
    assert payload["authorization_consumed"] is True
    assert payload["authorization_consumed_by_task"] == "AION-162"
    assert payload["authorization_consumed_by_primary_pr"] == 72
    assert (
        payload["authorization_consumed_by_primary_feature_commit"]
        == AION_162_PRIMARY_FEATURE_COMMIT
    )
    assert (
        payload["authorization_consumed_by_primary_merge_commit"] == AION_162_PRIMARY_MERGE_COMMIT
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
    assert payload["authorization_expired"] is True
    assert payload["authorization_reusable"] is False
    assert payload["cryptography_dependency_present"] is True
    assert payload["cryptography_dependency_specifier"] == ">=49.0.0,<50.0.0"
    assert payload["cryptography_dependency_count"] == 1
    assert payload["offline_identity_assertion_verification_state"] == "implemented_unintegrated"
    assert payload["request_authenticated"] is False
    assert payload["actor_context_applied"] is False
    assert payload["request_identity_context_applied"] is False
    assert payload["runtime_effect"] is False
    assert payload["replay_check_performed"] is False
    assert payload["replay_protection_required_before_request_integration"] is True


def test_aion163_authorization_payload_is_exactly_scoped() -> None:
    for relative in AION163_JSON_ARTIFACTS:
        payload = _json(relative)
        assert payload["task_id"] == "AION-163"
        assert payload["authorization_transaction_id"] == "AION-163-PA-0007"
        assert payload["approval_record_id"] == "AION-163-PA-0007"
        assert payload["parent_authorization_transaction_id"] == "AION-161-PA-0006"
        assert payload["candidate_id"] == "production-auth-identity-assertion-replay-protection"
        assert payload["workstream"] == "production-auth-verification-integrity"
        assert payload["implementation_task"] == "AION-164"
        assert (
            payload["authorization_scope"] == "persistent-identity-assertion-replay-protection-core"
        )
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS | IDENTITY_ASSERTION_REPLAY_PROTECTION_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in IDENTITY_ASSERTION_REPLAY_PROTECTION_FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert payload["approved_dependency_changes"] == []
        assert set(payload["approved_scope"]) == IDENTITY_ASSERTION_REPLAY_PROTECTION_APPROVED_SCOPE
        assert (
            set(payload["prohibited_scope"])
            == IDENTITY_ASSERTION_REPLAY_PROTECTION_PROHIBITED_SCOPE
        )
        assert payload["required_adr"] == AION163_AUTHORIZATION.required_adr
        assert (
            payload["replay_key_contract"]["schema_version"] == "identity-assertion-replay-key/v1"
        )
        assert payload["replay_key_contract"]["identity_input"] == ["issuer", "assertion_id"]
        assert payload["replay_key_contract"]["raw_issuer_persisted"] is False
        assert payload["replay_key_contract"]["raw_assertion_id_persisted"] is False
        assert (
            payload["atomic_claim_contract"]["primary_algorithm"]
            == "single_insert_unique_constraint"
        )
        assert payload["atomic_claim_contract"]["select_then_insert_primary_algorithm"] is False
        assert payload["retention_policy"]["minimum_retention_seconds"] == 86400
        assert payload["retention_policy"]["maximum_retention_seconds"] == 604800
        assert (
            payload["database_table_contract"]["table_name"]
            == "aion_identity_assertion_replay_claims"
        )
        assert payload["database_table_contract"]["auto_create_default"] is False
        assert payload["database_table_contract"]["test_auto_create_allowed"] is True
        assert payload["database_table_contract"]["production_auto_create_allowed"] is False
        assert payload["database_table_contract"]["migration_authorized"] is False


def test_aion163_is_only_active_authorization() -> None:
    validate_authorization_lifecycle_payloads(_canonical_records())
    aion161 = _payload_from_spec(AION161_AUTHORIZATION)
    assert aion161["authorization_active"] is False
    assert aion161["authorization_consumed"] is True
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
            lambda records: records.append(("unknown.json", _unknown_active_payload())),
            "unknown approved authorization record",
        ),
        (
            lambda records: records[5][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("authorization_reusable", True),
            "authorization_reusable must be false",
        ),
        (
            lambda records: records[5][1].__setitem__("authorization_expired", False),
            "authorization_expired must be true",
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
            lambda records: records[6][1].__setitem__(
                "parent_authorization_transaction_id", "AION-159-PA-0005"
            ),
            "parent_authorization_transaction_id mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("implementation_task", "AION-163"),
            "implementation_task mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("candidate_id", "production-auth-runtime"),
            "candidate_id mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("workstream", "production-auth-runtime"),
            "workstream mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "authorization_scope", "request-authentication"
            ),
            "authorization_scope mismatch",
        ),
        (
            lambda records: records[6][1].__setitem__("atomic_replay_claim_approved", False),
            "atomic_replay_claim_approved must be true",
        ),
        (
            lambda records: records[6][1].__setitem__("extra_replay_permission_approved", True),
            "approved permission set mismatch",
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
                "production_schema_auto_create_approved", True
            ),
            "production_schema_auto_create_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "test_only_schema_auto_create_approved", False
            ),
            "test_only_schema_auto_create_approved must be true",
        ),
        (
            lambda records: records[6][1].__setitem__("request_authentication_approved", True),
            "request_authentication_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "request_middleware_integration_approved", True
            ),
            "request_middleware_integration_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("actor_context_application_approved", True),
            "actor_context_application_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "request_identity_context_application_approved", True
            ),
            "request_identity_context_application_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("raw_assertion_persistence_approved", True),
            "raw_assertion_persistence_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "in_memory_runtime_replay_store_approved", True
            ),
            "in_memory_runtime_replay_store_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__(
                "background_cleanup_scheduler_approved", True
            ),
            "background_cleanup_scheduler_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("external_calls_approved", True),
            "external_calls_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("lockfile_approved", True),
            "lockfile_approved must be false",
        ),
        (
            lambda records: records[6][1].__setitem__("v02_tag_created", True),
            "v02_tag_created must be false",
        ),
    ],
)
def test_aion163_validator_rejects_bad_lifecycle(mutator: Any, match: str) -> None:
    records = _canonical_records()
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_aion163_docs_status_and_release_readiness_are_current() -> None:
    status = _text("docs/project-status.md")
    assert "Current authorization: AION-163-PA-0007 active for AION-164." in status
    assert "AION-161-PA-0006 consumed by AION-162 when merged." in status
    assert "persistent identity-assertion replay protection" in status
    readiness = _text("docs/release/v02-release-readiness-delta.md")
    assert "AION-163-PA-0007" in readiness
    assert "v02_release_ready=false" in readiness
    assert "v02_tag_created=false" in readiness
    assert "v02_release_created=false" in readiness


def test_aion163_does_not_change_protected_sources_or_add_release_artifacts() -> None:
    changed = _changed_files()
    for forbidden in PROTECTED_SOURCE_PATHS:
        assert not any(
            (path == forbidden or path.startswith(f"{forbidden}/"))
            and path not in AION164_IMPLEMENTATION_PATHS
            for path in changed
        )
    has_aion164_implementation_diff = any(path in changed for path in AION164_IMPLEMENTATION_PATHS)
    for path in AION164_IMPLEMENTATION_PATHS:
        if has_aion164_implementation_diff and (ROOT / path).exists():
            assert path in changed or not changed, path
    assert not any(path.endswith("package.json") for path in changed)
    assert not any(path.endswith("package-lock.json") for path in changed)
    assert not any(path.endswith("pnpm-lock.yaml") for path in changed)
    assert not any(path.endswith("yarn.lock") for path in changed)
    assert not any(path.endswith("bun.lockb") for path in changed)
    assert not any(
        "migration" in Path(path).name.lower() and path not in AION164_IMPLEMENTATION_PATHS
        for path in changed
    )
    assert not any(path.startswith("migrations/") for path in changed)


def test_aion163_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["PYTEST_CURRENT_TEST"] = env.get("PYTEST_CURRENT_TEST", "AION-163 focused script test")
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def test_aion163_does_not_create_v02_release_or_tag() -> None:
    tags = subprocess.run(
        ["git", "tag", "--list"], cwd=ROOT, capture_output=True, text=True, check=True
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
    if spec.approved_dependency_name is not None:
        payload["approved_dependency"] = {
            "name": spec.approved_dependency_name,
            "specifier": spec.approved_dependency_specifier,
            "manifest": spec.approved_dependency_manifest,
            "change_count": spec.approved_dependency_change_count,
        }
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
    working_tree = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMRT", "HEAD", "--"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    staged = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMRT", "--"],
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
        for line in [
            *diff.stdout.splitlines(),
            *working_tree.stdout.splitlines(),
            *staged.stdout.splitlines(),
            *untracked.stdout.splitlines(),
        ]
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
