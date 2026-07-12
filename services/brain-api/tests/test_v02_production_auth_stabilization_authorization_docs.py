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
    ACTIVE_AUTHORIZATION,
    ACTIVE_REQUIRED_SCOPE,
    APPROVAL_TRUE_KEYS,
    CANONICAL_FALSE_KEYS,
    HISTORICAL_AUTHORIZATION,
    HISTORICAL_REQUIRED_SCOPE,
    PROHIBITED_SCOPE,
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
    "examples/release/v02-production-auth-core-implementation-closeout.json",
    "examples/release/v02-production-auth-stabilization-authorization.json",
    "examples/release/v02-production-auth-stabilization-explicit-approval-record.json",
    "examples/release/v02-production-auth-stabilization-runtime-guard-renewal.json",
    "examples/release/v02-production-auth-stabilization-authorization-evidence-matrix.json",
    "operator-console-static/demo-data/v02-production-auth-core-implementation-closeout.json",
    "operator-console-static/demo-data/v02-production-auth-stabilization-authorization.json",
]

ACTIVE_JSON_ARTIFACTS = [
    relative for relative in JSON_ARTIFACTS if "stabilization" in relative
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


def test_v02_production_auth_stabilization_docs_exist_and_define_scope() -> None:
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
        "authorization_active=true",
        "authorization_consumed=false",
        "authorization_expired=false",
        "authorization_reusable=false",
        "production_auth_runtime_enabled=false",
    ]:
        assert required in transaction

    closeout = _text("docs/release/v02-production-auth-core-implementation-closeout.md")
    for required in [
        "authorization_transaction_id=AION-151-PA-0001",
        "authorization_active=false",
        "authorization_consumed=true",
        "authorization_consumed_by_pr=62",
        "authorization_expired=true",
        "authorization_reusable=false",
        "bc0614bcde19448b2a423614836bee3c06728c98",
    ]:
        assert required in closeout


def test_v02_production_auth_stabilization_json_is_exactly_scoped() -> None:
    for relative in ACTIVE_JSON_ARTIFACTS:
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
        assert payload["authorization_active"] is True
        assert payload["authorization_consumed"] is False
        assert payload["authorization_expired"] is False
        assert payload["authorization_reusable"] is False
        for key in APPROVAL_TRUE_KEYS:
            assert payload.get(key) is True, f"{relative}: {key}"
        for key in CANONICAL_FALSE_KEYS:
            assert payload.get(key) is False, f"{relative}: {key}"
        assert payload["runtime_guard_hold_active"] is True
        assert payload["runtime_no_go_status"] is True
        assert ACTIVE_REQUIRED_SCOPE <= set(payload["approved_scope"])
        assert PROHIBITED_SCOPE <= set(payload["prohibited_scope"])
        assert (
            payload["required_adr"]
            == "0144-v02-production-auth-core-stabilization-authorization.md"
        )
        assert payload["expiry"] == "AION-154 merged or authorization explicitly revoked"
        assert payload["required_gates"]
        assert payload["evidence_references"]
        assert payload["reviewer_roles"]


def test_v02_production_auth_stabilization_closes_aion151_lifecycle() -> None:
    closeout = _json("examples/release/v02-production-auth-core-implementation-closeout.json")
    consumed = closeout["consumed_authorization_record"]
    assert consumed["authorization_transaction_id"] == "AION-151-PA-0001"
    assert consumed["approval_record_id"] == "AION-151-PA-0001"
    assert consumed["candidate_id"] == "production-auth-core"
    assert consumed["implementation_task"] == "AION-152"
    assert consumed["authorization_scope"] == "disabled-production-auth-core"
    assert consumed["authorization_active"] is False
    assert consumed["authorization_consumed"] is True
    assert consumed["authorization_consumed_by_task"] == "AION-152"
    assert consumed["authorization_consumed_by_pr"] == 62
    assert (
        consumed["authorization_consumed_by_merge_commit"]
        == "bc0614bcde19448b2a423614836bee3c06728c98"
    )
    assert consumed["authorization_expired"] is True
    assert consumed["authorization_reusable"] is False
    assert HISTORICAL_REQUIRED_SCOPE <= set(consumed["approved_scope"])
    assert PROHIBITED_SCOPE <= set(consumed["prohibited_scope"])


def test_v02_production_auth_stabilization_validator_accepts_exact_lifecycle() -> None:
    validate_authorization_lifecycle_payloads(
        [
            ("historical.json", _payload_from_spec(HISTORICAL_AUTHORIZATION)),
            ("active.json", _payload_from_spec(ACTIVE_AUTHORIZATION)),
        ]
    )


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (
            lambda records: records.append(
                (
                    "duplicate-active.json",
                    {
                        **_payload_from_spec(ACTIVE_AUTHORIZATION),
                        "authorization_transaction_id": "AION-999-PA-0003",
                        "approval_record_id": "AION-999-PA-0003",
                    },
                )
            ),
            "unknown approved authorization record",
        ),
        (
            lambda records: records.append(
                (
                    "unknown-active.json",
                    {
                        **_payload_from_spec(ACTIVE_AUTHORIZATION),
                        "authorization_transaction_id": "AION-000-PA-0000",
                        "approval_record_id": "AION-000-PA-0000",
                    },
                )
            ),
            "unknown approved authorization record",
        ),
        (
            lambda records: records[0][1].__setitem__("authorization_active", True),
            "authorization_active must be false",
        ),
        (
            lambda records: records[0][1].update(
                {"authorization_expired": False, "authorization_reusable": True}
            ),
            "authorization_expired must be true",
        ),
        (
            lambda records: records[1][1].update(
                {"authorization_consumed": True, "authorization_expired": True}
            ),
            "authorization_consumed must be false",
        ),
        (
            lambda records: records[1][1].__setitem__(
                "authorization_scope", "disabled-production-auth-core-stabilization-and-login"
            ),
            "authorization_scope mismatch",
        ),
        (
            lambda records: records[1][1].__setitem__("implementation_task", "AION-155"),
            "implementation_task mismatch",
        ),
        (
            lambda records: records[1][1].__setitem__("production_auth_runtime_enabled", True),
            "production_auth_runtime_enabled must be false",
        ),
        (
            lambda records: records[1][1].__setitem__("implementation_go_status", False),
            "partial authorization approval true keys",
        ),
    ],
)
def test_v02_production_auth_stabilization_validator_rejects_bad_lifecycle(
    mutator: Any,
    match: str,
) -> None:
    records = [
        ("historical.json", _payload_from_spec(HISTORICAL_AUTHORIZATION)),
        ("active.json", _payload_from_spec(ACTIVE_AUTHORIZATION)),
    ]
    mutator(records)
    with pytest.raises(AssertionError, match=match):
        validate_authorization_lifecycle_payloads(records)


def test_v02_production_auth_stabilization_scripts_are_executable_and_pass() -> None:
    env = os.environ.copy()
    env["AION_V02_PRODUCTION_AUTH_STABILIZATION_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK"] = "1"
    env["AION_V02_PRODUCTION_AUTH_RUNTIME_GUARD_HOLD_SKIP_FULL_CHECK"] = "1"
    env["AION_PRODUCTION_AUTH_CORE_RUNTIME_HOLD_SKIP_FULL_CHECK"] = "1"
    env["PYTEST_CURRENT_TEST"] = env.get(
        "PYTEST_CURRENT_TEST", "AION-153 focused script test"
    )
    for relative in SCRIPTS:
        path = ROOT / relative
        assert path.exists(), relative
        assert path.stat().st_mode & stat.S_IXUSR, relative
        subprocess.run([str(path)], cwd=ROOT, check=True, env=env)


def test_v02_production_auth_stabilization_does_not_change_forbidden_sources() -> None:
    changed = _changed_files()
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
        "authorization_consumed_by_merge_commit": spec.authorization_consumed_by_merge_commit,
        "authorization_expired": spec.authorization_expired,
        "authorization_reusable": spec.authorization_reusable,
        "runtime_guard_hold_active": True,
        "runtime_no_go_status": True,
        "approved_scope": list(
            ACTIVE_REQUIRED_SCOPE
            if spec.transaction_id == ACTIVE_AUTHORIZATION.transaction_id
            else HISTORICAL_REQUIRED_SCOPE
        ),
        "prohibited_scope": list(PROHIBITED_SCOPE),
        "required_adr": spec.required_adr,
        "required_gates": ["unit-test-gate"],
        "evidence_references": ["unit-test-evidence"],
        "reviewer_roles": ["security reviewer"],
        "expiry": spec.expiry,
        "revocation_path": "unit test revocation path",
    }
    for key in APPROVAL_TRUE_KEYS:
        payload[key] = True
    for key in CANONICAL_FALSE_KEYS:
        payload[key] = False
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
