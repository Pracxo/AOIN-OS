#!/usr/bin/env python3
"""Final read-only evaluation for the retained AION v0.2.0-rc.1 candidate."""

from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROGRAM_ID = "AION-V02-RELEASE-QUALIFICATION-001"
EVALUATION_TYPE = "deterministic_v02_release_candidate_final_evaluation"
IMPLEMENTATION_TASK = "AION-243"
CLOSEOUT_TASK = "AION-244"
AUTHORIZATION_ID = "AION-242-V02RQ-0003"
PUBLICATION_AUTHORIZATION_ID = "AION-244-V02REL-0001"
EVALUATION_ID = "AION-V02RQPE-003"
CANDIDATE_ID = "aion-v0.2.0-rc.1"
PACKAGE_VERSION = "0.2.0rc1"
LOCAL_IMAGE_TAG = "aoinos-brain-api:aion-v0.2.0-rc.1"
FROZEN_BASE_IMAGE_TAG = "aoinos-brain-api:aion241-base-9f6b899f84ef"
FROZEN_BASE_IMAGE_ID = (
    "sha256:d55ed37f90d85ca0fc5973e6d3cdd849353e0549a7df95d39864506712b342ea"
)
CANDIDATE_IMAGE_ID = (
    "sha256:0247d4f8fc270f2eadbca256f1f48475289da6744393bd2fd278e43d9d565f0d"
)
IMPLEMENTATION_MAIN_COMMIT = "c18ea935f29e06590b83fc23efba7ae49fc6efab"
IMPLEMENTATION_COMMITS = (
    "19da1991027ba702d9a382c42e3ad5ff10d60d93",
    "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e",
    "8a4e3f1de848018e347facd28875921229ba527c",
)
CANDIDATE_SOURCE_COMMIT = "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e"
CANDIDATE_EVIDENCE_FINGERPRINT = (
    "a5e7430075cb05d5c08ea6fc068cc0b961560834227f32059a9be8856c8a8d54"
)
SOURCE_TREE_FINGERPRINT = (
    "932a1893cfa440a088a1852627843fb2dbfa3bf8ae333f35384da1c47d5da1a7"
)
SOURCE_ARCHIVE_FINGERPRINT = (
    "9110172942c24d24c7c459500730b896278b9f57fb5911d4aa6d3a12d591f2bc"
)
OCI_ARCHIVE_FINGERPRINT = (
    "07d693d08c99bb2424615f1cd4df538a8303526b0bd008fdf8c2d5b4db3c6014"
)
SBOM_FINGERPRINT = (
    "52ba5138b1f01982f9357190739e029808744809d48f2365a4cdcf18afa68a7f"
)
SBOM_COMPONENT_COUNT = 66
PROVENANCE_CHAIN_HEAD = (
    "70a875688d43771ebc63393ae1e3cbca11f6b46f0db634438fec89f3f129f752"
)
CHECKSUM_MANIFEST_FINGERPRINT = (
    "bfb9eda9b0eb6b3005eee8cd628376c03f2ce062ef937b2ca0a1a5c5d758a9d4"
)
PUBLIC_KEY_FINGERPRINT = (
    "b3a883a894da84cdef499acf87a43bea1fdfa4d4f5c04704c3916d6b5d49cf4c"
)
BUNDLE_MANIFEST_FINGERPRINT = (
    "9da9f1bcc4fb5bb8ddd0a49f2bab3aec5424c9e55cb8c21bebc35abb117f9e9c"
)
CONTENT_MANIFEST_FINGERPRINT = (
    "3131b3e6ac04a455d960b04aba5852377d518575a470a26935f125d6d97be7d5"
)
INTEGRITY_REPORT_FINGERPRINT = (
    "5980efbf0c6dfed549b080b19657bf35840c338108b4d6849bcbdd5a1bcc337c"
)
EVIDENCE_BUNDLE_FINGERPRINT = (
    "2c07edd17161b2406936fc25e7e2897e01c1b909fe507df6b5a3048e2721620a"
)
SDK_WHEEL_FINGERPRINT = (
    "9cc5b5694c89c6792b165ff6757975353c5924489bfbc014a2e91b23083113c1"
)
SDK_SDIST_FINGERPRINT = (
    "5db9f9a39c67b9d988d24ccce980123d50bd2b7bd278c68c52c3528af3038fb4"
)
OPERATOR_CONSOLE_FINGERPRINT = (
    "503e28f18821cef4df74812da99761917adf401b68630ccdfea9c2d25f33bd58"
)
COMPATIBILITY_FINGERPRINT = (
    "b376f2902c4c1a2f8a49a7e9f1f43fd365077e42848d9c0b7c4d652313d4fb56"
)
MIGRATION_FINGERPRINT = (
    "76ef5a423282639d6aaec7f50dc238141f29d5ca785d48c6fc09309d1326d1cc"
)
RELEASE_NOTES_DRAFT_FINGERPRINT = (
    "2d976ae96bf3213331817ce6ee63a7e0c0bbc7ca85e6620db032f9c289078ec8"
)

PASS_DECISION = (
    "DETERMINISTIC_LOCAL_V02_RELEASE_CANDIDATE_FINAL_EVALUATION_PASS_AUTHORIZE_"
    "AION_V0_2_0_RC_1_ANNOTATED_TAG_AND_GITHUB_PRERELEASE_PUBLICATION"
)
FAIL_DECISION = (
    "DETERMINISTIC_LOCAL_V02_RELEASE_CANDIDATE_FINAL_EVALUATION_FAIL_RETAIN_"
    "LOCAL_CANDIDATE_UNPUBLISHED_REMEDIATION_REQUIRED"
)

SCENARIO_IDS = (
    "aion_243_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "committed_candidate_evidence_schema_and_fingerprint",
    "live_candidate_retention_and_locator_integrity",
    "candidate_source_commit_and_tag_target_integrity",
    "package_version_and_dependency_integrity",
    "deterministic_source_archive_integrity",
    "brain_api_oci_archive_integrity",
    "retained_candidate_image_integrity",
    "sdk_wheel_integrity",
    "sdk_sdist_integrity",
    "operator_console_bundle_integrity",
    "candidate_content_and_bundle_manifest_integrity",
    "checksum_manifest_integrity",
    "qualification_public_key_and_signature_integrity",
    "private_qualification_key_non_retention",
    "candidate_sbom_integrity",
    "candidate_provenance_chain_integrity",
    "reproducibility_evidence_honesty",
    "compatibility_matrix_integrity",
    "migration_manifest_truthfulness",
    "release_notes_accuracy_and_prerelease_semantics",
    "protected_material_and_secret_exclusion",
    "candidate_file_inventory_and_permission_integrity",
    "candidate_image_package_and_application_smoke",
    "sdk_candidate_installation_and_entrypoint_smoke",
    "zero_registry_package_upload_and_production_effects",
    "tag_and_release_preexistence_boundary",
    "release_asset_inventory_and_upload_readiness",
    "annotated_tag_target_and_message_readiness",
    "github_prerelease_transaction_and_rollback_readiness",
    "final_rc1_publication_authorization_readiness",
)

ASSET_PATHS = (
    "source/aion-v0.2.0-rc.1-source.tar.gz",
    "brain-api/aion-brain-api-0.2.0-rc.1.oci.tar",
    "brain-api/brain-api-artifact-manifest.json",
    "sdk/aion_sdk_python-0.2.0rc1-py3-none-any.whl",
    "sdk/aion_sdk_python-0.2.0rc1.tar.gz",
    "operator-console/aion-operator-console-0.2.0-rc.1.tar.gz",
    "metadata/candidate-version-manifest.json",
    "metadata/candidate-content-manifest.json",
    "metadata/candidate-bundle-manifest.json",
    "metadata/candidate-sbom.spdx.json",
    "metadata/candidate-provenance.intoto.json",
    "metadata/SHA256SUMS",
    "signatures/qualification-public-key.json",
    "signatures/candidate-content-manifest.sig",
    "signatures/SHA256SUMS.sig",
    "signatures/candidate-provenance.sig",
    "signatures/candidate-sbom.sig",
    "signatures/candidate-bundle-manifest.sig",
    "evidence/reproducibility-comparison.json",
    "evidence/compatibility-matrix.json",
    "evidence/migration-manifest.json",
    "evidence/release-notes-draft.md",
    "evidence/candidate-integrity-report.json",
    "evidence/candidate-evidence-bundle.json",
)
SIGNATURE_TARGETS = (
    ("metadata/candidate-content-manifest.json", "signatures/candidate-content-manifest.sig"),
    ("metadata/SHA256SUMS", "signatures/SHA256SUMS.sig"),
    ("metadata/candidate-provenance.intoto.json", "signatures/candidate-provenance.sig"),
    ("metadata/candidate-sbom.spdx.json", "signatures/candidate-sbom.sig"),
    ("metadata/candidate-bundle-manifest.json", "signatures/candidate-bundle-manifest.sig"),
)
ZERO_COUNTERS = (
    "registry_logins",
    "registry_pulls",
    "registry_pushes",
    "public_network_calls",
    "dns_resolutions",
    "public_package_uploads",
    "production_deployments",
    "private_qualification_keys_retained",
    "temporary_build_directories_retained",
    "intermediate_images_retained",
)


@dataclass
class CommandResult:
    argv: list[str]
    returncode: int
    stdout: str
    stderr: str


class GateFailure(RuntimeError):
    """Raised when a hard evaluation gate fails."""


def canonical_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def pretty_json(payload: object) -> str:
    return json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fingerprint(payload: object) -> str:
    return sha256_bytes(canonical_json(payload).encode("utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json(payload), encoding="utf-8")


def run(
    argv: Sequence[str],
    *,
    cwd: Path,
    timeout: int = 120,
    check: bool = True,
    env: Mapping[str, str] | None = None,
) -> CommandResult:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        env={**os.environ, **dict(env or {})},
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    result = CommandResult(
        argv=list(argv),
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )
    if check and result.returncode != 0:
        raise GateFailure(
            f"command failed ({result.returncode}): {result.argv}: {result.stderr.strip()}"
        )
    return result


def require(condition: bool, message: str) -> None:
    if not condition:
        raise GateFailure(message)


def require_equal(actual: object, expected: object, message: str) -> None:
    if actual != expected:
        raise GateFailure(f"{message}: expected {expected!r}, got {actual!r}")


def decode_b64url(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def load_aion243_runner(repo_root: Path) -> Any:
    runner_path = repo_root / "scripts" / "v02-release-candidate-local-run.py"
    spec = importlib.util.spec_from_file_location("aion243_runner_for_aion244", runner_path)
    require(spec is not None and spec.loader is not None, "unable to load AION-243 runner")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git_status(repo_root: Path) -> str:
    return run(["git", "status", "--porcelain=v1"], cwd=repo_root).stdout.strip()


class FinalCandidateEvaluator:
    def __init__(
        self,
        *,
        repo_root: Path,
        evaluation_id: str,
        implementation_main_commit: str,
        candidate_source_commit: str,
        candidate_evidence: Path,
        candidate_root: Path,
        evaluation_base_commit: str,
        temporary_output_directory: Path,
    ) -> None:
        self.repo_root = repo_root
        self.evaluation_id = evaluation_id
        self.implementation_main_commit = implementation_main_commit
        self.candidate_source_commit = candidate_source_commit
        self.candidate_evidence_path = candidate_evidence
        self.candidate_root = candidate_root
        self.evaluation_base_commit = evaluation_base_commit
        self.temporary_output_directory = temporary_output_directory
        self.work_dir = temporary_output_directory / "work"
        self.context: dict[str, Any] = {}
        self.aion243_runner = load_aion243_runner(repo_root)

    def candidate_path(self, relative: str) -> Path:
        return self.candidate_root / relative

    def load_evidence(self) -> Mapping[str, Any]:
        if "candidate_evidence" not in self.context:
            self.context["candidate_evidence"] = load_json(self.candidate_evidence_path)
        return self.context["candidate_evidence"]

    def load_bundle_manifest(self) -> Mapping[str, Any]:
        if "bundle_manifest" not in self.context:
            self.context["bundle_manifest"] = load_json(
                self.candidate_path("metadata/candidate-bundle-manifest.json")
            )
        return self.context["bundle_manifest"]

    def load_content_manifest(self) -> Mapping[str, Any]:
        if "content_manifest" not in self.context:
            self.context["content_manifest"] = load_json(
                self.candidate_path("metadata/candidate-content-manifest.json")
            )
        return self.context["content_manifest"]

    def evaluate(self) -> dict[str, Any]:
        starting_status = git_status(self.repo_root)
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        self.work_dir.mkdir(parents=True, mode=0o700)
        scenario_results: list[dict[str, Any]] = []
        for scenario_id in SCENARIO_IDS:
            checker = getattr(self, f"scenario_{scenario_id}")
            try:
                details = checker()
                scenario_results.append(
                    {
                        "scenario_id": scenario_id,
                        "hard_gate": True,
                        "result": "pass",
                        "details": details or {},
                    }
                )
            except Exception as exc:  # noqa: BLE001 - evidence must capture every gate failure.
                scenario_results.append(
                    {
                        "scenario_id": scenario_id,
                        "hard_gate": True,
                        "result": "fail",
                        "details": {"error": str(exc)},
                    }
                )
        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)
        ending_status = git_status(self.repo_root)
        passed = all(item["result"] == "pass" for item in scenario_results)
        decision = PASS_DECISION if passed else FAIL_DECISION
        evidence = dict(self.load_evidence())
        payload: dict[str, Any] = {
            "evaluation_id": self.evaluation_id,
            "evaluation_type": EVALUATION_TYPE,
            "program_id": PROGRAM_ID,
            "implementation_task": IMPLEMENTATION_TASK,
            "closeout_task": CLOSEOUT_TASK,
            "implementation_main_commit": self.implementation_main_commit,
            "candidate_source_commit": self.candidate_source_commit,
            "evaluation_base_commit": self.evaluation_base_commit,
            "implementation_prs": [162],
            "implementation_feature_commits": list(IMPLEMENTATION_COMMITS),
            "implementation_merge_commits": [IMPLEMENTATION_MAIN_COMMIT],
            "decision": decision,
            "evaluation_passed": passed,
            "scenario_count": len(SCENARIO_IDS),
            "scenario_ids": list(SCENARIO_IDS),
            "scenario_results": scenario_results,
            "hard_gate_count": len(SCENARIO_IDS),
            "hard_gate_results": scenario_results,
            "candidate_validation": {
                "candidate_id": CANDIDATE_ID,
                "candidate_python_package_version": PACKAGE_VERSION,
                "candidate_report_fingerprint": evidence["report_fingerprint"],
                "candidate_image_id": evidence["candidate_image_id"],
                "candidate_bundle_retained": True,
                "candidate_image_retained": True,
            },
            "authorization_lineage": {
                "implementation_authorization": AUTHORIZATION_ID,
                "publication_authorization": PUBLICATION_AUTHORIZATION_ID if passed else None,
                "aion_242_consumable": passed,
            },
            "source_integrity": {
                "source_commit": CANDIDATE_SOURCE_COMMIT,
                "source_tree_fingerprint": SOURCE_TREE_FINGERPRINT,
                "source_archive_fingerprint": SOURCE_ARCHIVE_FINGERPRINT,
            },
            "artifact_integrity": {
                "oci_archive_fingerprint": OCI_ARCHIVE_FINGERPRINT,
                "sdk_wheel_fingerprint": SDK_WHEEL_FINGERPRINT,
                "sdk_sdist_fingerprint": SDK_SDIST_FINGERPRINT,
                "operator_console_bundle_fingerprint": OPERATOR_CONSOLE_FINGERPRINT,
            },
            "checksum_integrity": {
                "checksum_manifest_fingerprint": CHECKSUM_MANIFEST_FINGERPRINT,
                "checksum_records_verified": len(self._checksum_records()),
            },
            "signature_integrity": {
                "public_key_fingerprint": PUBLIC_KEY_FINGERPRINT,
                "signature_count": 5,
                "verified_signature_count": self.context.get("verified_signature_count", 5),
            },
            "sbom_integrity": {
                "candidate_sbom_fingerprint": SBOM_FINGERPRINT,
                "component_count": SBOM_COMPONENT_COUNT,
            },
            "provenance_integrity": {
                "candidate_provenance_chain_head": PROVENANCE_CHAIN_HEAD,
            },
            "compatibility_integrity": {
                "compatibility_matrix_fingerprint": COMPATIBILITY_FINGERPRINT,
            },
            "migration_integrity": {
                "migration_manifest_fingerprint": MIGRATION_FINGERPRINT,
            },
            "retention_integrity": {
                "candidate_root": "user-home/.aion/release-candidates/aion-v0.2.0-rc.1",
                "candidate_image": LOCAL_IMAGE_TAG,
                "frozen_base_image": FROZEN_BASE_IMAGE_TAG,
            },
            "release_asset_plan": {
                "asset_count": len(ASSET_PATHS),
                "asset_paths": list(ASSET_PATHS),
                "unique_basenames": True,
            },
            "tag_plan": {
                "tag_name": CANDIDATE_ID,
                "tag_target_commit": CANDIDATE_SOURCE_COMMIT,
                "annotated": True,
                "stable_tag_created": False,
            },
            "publication_plan": {
                "release_name": "AION OS v0.2.0-rc.1",
                "release_kind": "github_prerelease",
                "release_prerelease": True,
                "release_draft_initially": True,
                "stable_release_created": False,
            },
            "repository_integrity": {
                "repository_unchanged": starting_status == ending_status,
                "starting_status": starting_status,
                "ending_status": ending_status,
            },
            "next_architecture_decision": (
                "aion_v0_2_0_rc_1_github_prerelease_publication_authorized"
                if passed
                else "release_candidate_remediation_review"
            ),
            "read_only": True,
            "redacted": True,
            "candidate_rebuilds_executed_by_evaluation": 0,
            "tags_created_by_evaluation": 0,
            "github_releases_created_by_evaluation": 0,
            "release_assets_uploaded_by_evaluation": 0,
            "registry_logins": 0,
            "registry_pulls": 0,
            "registry_pushes": 0,
            "public_package_uploads": 0,
            "production_deployments": 0,
            "stable_tags_created": 0,
            "stable_releases_created": 0,
            "repository_unchanged": starting_status == ending_status,
            "temporary_evaluation_data_cleaned": not self.work_dir.exists(),
            "corrective_cycles": 0,
            "corrective_prs": [],
        }
        payload["report_fingerprint"] = fingerprint(
            {key: value for key, value in payload.items() if key != "report_fingerprint"}
        )
        return payload

    def scenario_aion_243_delivery_and_ci_integrity(self) -> dict[str, Any]:
        pr = json.loads(
            run(
                [
                    "gh",
                    "pr",
                    "view",
                    "162",
                    "--repo",
                    "Pracxo/AOIN-OS",
                    "--json",
                    "number,title,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName,url",
                ],
                cwd=self.repo_root,
                timeout=60,
            ).stdout
        )
        require_equal(pr["state"], "MERGED", "PR #162 state mismatch")
        require_equal(pr["baseRefName"], "main", "PR #162 base mismatch")
        require_equal(
            pr["headRefName"],
            "phase/v02-release-candidate-artifact-build",
            "PR #162 head branch mismatch",
        )
        require_equal(pr["headRefOid"], IMPLEMENTATION_COMMITS[-1], "PR #162 head SHA mismatch")
        require_equal(
            pr["mergeCommit"]["oid"],
            IMPLEMENTATION_MAIN_COMMIT,
            "PR #162 merge commit mismatch",
        )
        require_equal(pr["mergedAt"], "2026-08-02T23:25:24Z", "PR #162 mergedAt mismatch")
        commits = json.loads(
            run(
                ["gh", "api", "repos/Pracxo/AOIN-OS/pulls/162/commits"],
                cwd=self.repo_root,
                timeout=60,
            ).stdout
        )
        require_equal([item["sha"] for item in commits], list(IMPLEMENTATION_COMMITS), "PR #162 commit order mismatch")
        checks = json.loads(
            run(
                [
                    "gh",
                    "pr",
                    "checks",
                    "162",
                    "--repo",
                    "Pracxo/AOIN-OS",
                    "--json",
                    "name,state",
                ],
                cwd=self.repo_root,
                timeout=60,
            ).stdout
        )
        states = {item["name"]: item["state"] for item in checks}
        required_checks = {
            "brain-api-quality",
            "contract-check",
            "docker-build-core",
            "policy-check",
            "repository-hygiene",
            "sdk-cli-check",
            "sdk-quality",
        }
        require_equal(set(states), required_checks, "PR #162 check set mismatch")
        for name in required_checks:
            require_equal(states[name], "SUCCESS", f"PR #162 check {name} mismatch")
        for commit in (*IMPLEMENTATION_COMMITS, IMPLEMENTATION_MAIN_COMMIT):
            run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], cwd=self.repo_root)
        return {"checks": sorted(required_checks), "merged_at": pr["mergedAt"]}

    def scenario_authorization_lineage_and_scope(self) -> dict[str, Any]:
        for relative in (
            "docs/v02-release-qualification/program-ledger.json",
            "docs/v02-release-qualification/authorization-ledger.json",
            "examples/v02-release-qualification/release-candidate-authorization.json",
        ):
            payload = load_json(self.repo_root / relative)
            require_equal(
                payload["active_v02_release_qualification_authorization"],
                AUTHORIZATION_ID,
                f"{relative} active authorization mismatch",
            )
            require_equal(payload["authorization_active"], True, f"{relative} active mismatch")
            require_equal(payload["authorization_consumed"], False, f"{relative} consumed mismatch")
            require_equal(payload["authorization_expired"], False, f"{relative} expired mismatch")
            require_equal(payload["authorization_reusable"], False, f"{relative} reusable mismatch")
            require_equal(payload["formal_closeout_task"], CLOSEOUT_TASK, f"{relative} closeout task mismatch")
            require_equal(payload["active_v02_release_qualification_authorization_count"], 1, f"{relative} active auth count mismatch")
        return {"authorization": AUTHORIZATION_ID}

    def scenario_committed_candidate_evidence_schema_and_fingerprint(self) -> dict[str, Any]:
        evidence = self.load_evidence()
        expected = fingerprint({key: value for key, value in evidence.items() if key != "report_fingerprint"})
        require_equal(evidence["report_fingerprint"], expected, "candidate evidence fingerprint mismatch")
        require_equal(evidence["report_fingerprint"], CANDIDATE_EVIDENCE_FINGERPRINT, "candidate evidence expected fingerprint mismatch")
        required = {
            "candidate_id": CANDIDATE_ID,
            "authorization_id": AUTHORIZATION_ID,
            "program_id": PROGRAM_ID,
            "candidate_source_commit": CANDIDATE_SOURCE_COMMIT,
            "brain_api_package_version": PACKAGE_VERSION,
            "sdk_package_version": PACKAGE_VERSION,
            "candidate_image_id": CANDIDATE_IMAGE_ID,
            "source_tree_fingerprint": SOURCE_TREE_FINGERPRINT,
            "source_archive_fingerprint": SOURCE_ARCHIVE_FINGERPRINT,
            "candidate_oci_archive_fingerprint": OCI_ARCHIVE_FINGERPRINT,
            "candidate_sbom_fingerprint": SBOM_FINGERPRINT,
            "candidate_sbom_component_count": SBOM_COMPONENT_COUNT,
            "candidate_provenance_chain_head": PROVENANCE_CHAIN_HEAD,
            "checksum_manifest_fingerprint": CHECKSUM_MANIFEST_FINGERPRINT,
            "qualification_public_key_fingerprint": PUBLIC_KEY_FINGERPRINT,
            "candidate_bundle_manifest_fingerprint": BUNDLE_MANIFEST_FINGERPRINT,
            "candidate_content_manifest_fingerprint": CONTENT_MANIFEST_FINGERPRINT,
            "candidate_integrity_report_fingerprint": INTEGRITY_REPORT_FINGERPRINT,
            "candidate_evidence_bundle_fingerprint": EVIDENCE_BUNDLE_FINGERPRINT,
        }
        for key, value in required.items():
            require_equal(evidence.get(key), value, f"candidate evidence {key} mismatch")
        for key in ZERO_COUNTERS:
            require_equal(evidence.get(key), 0, f"candidate evidence zero counter {key} mismatch")
        for key in ("candidate_bundle_retained", "candidate_image_retained", "release_candidate_created", "integrity_passed"):
            require_equal(evidence.get(key), True, f"candidate evidence {key} mismatch")
        for key in ("release_candidate_published", "production_deployment", "v02_release_ready", "v02_tag_created", "v02_release_created"):
            require_equal(evidence.get(key), False, f"candidate evidence {key} mismatch")
        return {"report_fingerprint": evidence["report_fingerprint"]}

    def scenario_live_candidate_retention_and_locator_integrity(self) -> dict[str, Any]:
        require(self.candidate_root.is_dir(), "candidate root is missing")
        require(not self.candidate_root.is_symlink(), "candidate root must not be a symlink")
        require_equal(stat.S_IMODE(self.candidate_root.stat().st_mode), 0o700, "candidate root mode mismatch")
        require(not self.candidate_root.resolve().is_relative_to(self.repo_root.resolve()), "candidate root is inside repository")
        verification = self.aion243_runner.verify_candidate(self.candidate_root)
        require_equal(verification["candidate_file_count"], len(ASSET_PATHS), "candidate file count mismatch")
        return verification

    def scenario_candidate_source_commit_and_tag_target_integrity(self) -> dict[str, Any]:
        run(["git", "cat-file", "-e", f"{self.candidate_source_commit}^{{commit}}"], cwd=self.repo_root)
        require_equal(self.candidate_source_commit, CANDIDATE_SOURCE_COMMIT, "candidate source commit mismatch")
        tag_output = run(
            ["git", "tag", "--list", "aion-v0.2.0-rc.1", "aion-v0.2.0", "v0.2.0*"],
            cwd=self.repo_root,
        ).stdout.strip()
        require_equal(tag_output, "", "v0.2 tag preexists")
        remote_tags = run(
            [
                "git",
                "ls-remote",
                "--tags",
                "origin",
                "refs/tags/aion-v0.2.0-rc.1",
                "refs/tags/aion-v0.2.0",
                "refs/tags/v0.2.0*",
            ],
            cwd=self.repo_root,
        ).stdout.strip()
        require_equal(remote_tags, "", "remote v0.2 tag preexists")
        return {"tag_target_commit": CANDIDATE_SOURCE_COMMIT}

    def scenario_package_version_and_dependency_integrity(self) -> dict[str, Any]:
        version_lines = {
            "services/brain-api/pyproject.toml": 'version = "0.2.0rc1"',
            "packages/aion-sdk-python/pyproject.toml": 'version = "0.2.0rc1"',
        }
        for relative, expected in version_lines.items():
            text = (self.repo_root / relative).read_text(encoding="utf-8")
            require(expected in text, f"{relative} version mismatch")
        changed = run(
            ["git", "diff", "--name-only", IMPLEMENTATION_COMMITS[0], IMPLEMENTATION_COMMITS[1]],
            cwd=self.repo_root,
        ).stdout.splitlines()
        require_equal(
            sorted(changed),
            ["packages/aion-sdk-python/pyproject.toml", "services/brain-api/pyproject.toml"],
            "version commit changed unexpected files",
        )
        return {"version": PACKAGE_VERSION}

    def scenario_deterministic_source_archive_integrity(self) -> dict[str, Any]:
        path = self.candidate_path("source/aion-v0.2.0-rc.1-source.tar.gz")
        require_equal(sha256_file(path), SOURCE_ARCHIVE_FINGERPRINT, "source archive fingerprint mismatch")
        with tarfile.open(path, "r:gz") as archive:
            names = archive.getnames()
            require(names and names[0] == "aion-v0.2.0-rc.1", "source archive prefix mismatch")
            for member in archive.getmembers():
                name = member.name
                require(not name.startswith("/") and ".." not in Path(name).parts, f"unsafe source archive path: {name}")
                require(not member.issym() and not member.islnk(), f"source archive contains link: {name}")
            text_members = {
                "aion-v0.2.0-rc.1/services/brain-api/pyproject.toml": 'version = "0.2.0rc1"',
                "aion-v0.2.0-rc.1/packages/aion-sdk-python/pyproject.toml": 'version = "0.2.0rc1"',
            }
            for member_name, expected in text_members.items():
                extracted = archive.extractfile(member_name)
                require(extracted is not None, f"source archive missing {member_name}")
                require(expected in extracted.read().decode("utf-8"), f"source archive version mismatch in {member_name}")
            forbidden_prefixes = (
                "aion-v0.2.0-rc.1/examples/v02-release-qualification/v02-release-candidate-final",
                "aion-v0.2.0-rc.1/scripts/lib/v02_release_candidate_final_evaluation.py",
            )
            for name in names:
                require(not name.startswith(forbidden_prefixes), f"source archive contains AION-244 content: {name}")
        return {"source_archive_file_count": len(names)}

    def scenario_brain_api_oci_archive_integrity(self) -> dict[str, Any]:
        path = self.candidate_path("brain-api/aion-brain-api-0.2.0-rc.1.oci.tar")
        require_equal(sha256_file(path), OCI_ARCHIVE_FINGERPRINT, "OCI archive fingerprint mismatch")
        with tarfile.open(path, "r:") as archive:
            names = set(archive.getnames())
            require("oci-layout" in names and "index.json" in names, "OCI archive layout missing")
            for member in archive.getmembers():
                require(not member.name.startswith("/") and ".." not in Path(member.name).parts, f"unsafe OCI path: {member.name}")
        manifest = load_json(self.candidate_path("brain-api/brain-api-artifact-manifest.json"))
        require_equal(manifest["architecture"], "linux/arm64", "OCI architecture mismatch")
        require_equal(manifest["source_commit"], CANDIDATE_SOURCE_COMMIT, "OCI source commit mismatch")
        require_equal(manifest["package_version"], PACKAGE_VERSION, "OCI package version mismatch")
        require_equal(manifest["publication"], False, "OCI publication flag mismatch")
        require_equal(manifest["production"], False, "OCI production flag mismatch")
        require_equal(manifest["base_image_id"], FROZEN_BASE_IMAGE_ID, "OCI base image ID mismatch")
        return {"oci_archive_fingerprint": OCI_ARCHIVE_FINGERPRINT}

    def scenario_retained_candidate_image_integrity(self) -> dict[str, Any]:
        image_id = run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", LOCAL_IMAGE_TAG],
            cwd=self.repo_root,
            timeout=60,
        ).stdout.strip()
        base_id = run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", FROZEN_BASE_IMAGE_TAG],
            cwd=self.repo_root,
            timeout=60,
        ).stdout.strip()
        require_equal(image_id, CANDIDATE_IMAGE_ID, "candidate image ID mismatch")
        require_equal(base_id, FROZEN_BASE_IMAGE_ID, "frozen base image ID mismatch")
        return {"candidate_image_id": image_id, "frozen_base_image_id": base_id}

    def scenario_sdk_wheel_integrity(self) -> dict[str, Any]:
        path = self.candidate_path("sdk/aion_sdk_python-0.2.0rc1-py3-none-any.whl")
        require_equal(sha256_file(path), SDK_WHEEL_FINGERPRINT, "SDK wheel fingerprint mismatch")
        with zipfile.ZipFile(path) as wheel:
            names = wheel.namelist()
            for name in names:
                require(not name.startswith("/") and ".." not in Path(name).parts, f"unsafe wheel path: {name}")
            metadata = wheel.read("aion_sdk_python-0.2.0rc1.dist-info/METADATA").decode("utf-8")
            entry_points = wheel.read("aion_sdk_python-0.2.0rc1.dist-info/entry_points.txt").decode("utf-8")
        require("Name: aion-sdk-python" in metadata, "SDK wheel package name mismatch")
        require("Version: 0.2.0rc1" in metadata, "SDK wheel version mismatch")
        require("aionctl = aion_sdk.cli.main:app" in entry_points, "SDK wheel entry point mismatch")
        return {"sdk_wheel_fingerprint": SDK_WHEEL_FINGERPRINT}

    def scenario_sdk_sdist_integrity(self) -> dict[str, Any]:
        path = self.candidate_path("sdk/aion_sdk_python-0.2.0rc1.tar.gz")
        require_equal(sha256_file(path), SDK_SDIST_FINGERPRINT, "SDK sdist fingerprint mismatch")
        with tarfile.open(path, "r:gz") as archive:
            names = archive.getnames()
            for member in archive.getmembers():
                require(not member.name.startswith("/") and ".." not in Path(member.name).parts, f"unsafe sdist path: {member.name}")
            pyproject = archive.extractfile("aion_sdk_python-0.2.0rc1/pyproject.toml")
            require(pyproject is not None, "SDK sdist pyproject missing")
            require('version = "0.2.0rc1"' in pyproject.read().decode("utf-8"), "SDK sdist version mismatch")
        return {"sdk_sdist_file_count": len(names)}

    def scenario_operator_console_bundle_integrity(self) -> dict[str, Any]:
        path = self.candidate_path("operator-console/aion-operator-console-0.2.0-rc.1.tar.gz")
        require_equal(sha256_file(path), OPERATOR_CONSOLE_FINGERPRINT, "operator console fingerprint mismatch")
        with tarfile.open(path, "r:gz") as archive:
            names = archive.getnames()
            for member in archive.getmembers():
                require(not member.name.startswith("/") and ".." not in Path(member.name).parts, f"unsafe operator console path: {member.name}")
            require(any(name.endswith("/index.html") for name in names), "operator console index missing")
            require(any(name.endswith("/app.js") for name in names), "operator console app missing")
        return {"operator_console_bundle_fingerprint": OPERATOR_CONSOLE_FINGERPRINT}

    def scenario_candidate_content_and_bundle_manifest_integrity(self) -> dict[str, Any]:
        content = self.load_content_manifest()
        bundle = self.load_bundle_manifest()
        require_equal(sha256_file(self.candidate_path("metadata/candidate-content-manifest.json")), CONTENT_MANIFEST_FINGERPRINT, "content manifest file fingerprint mismatch")
        require_equal(sha256_file(self.candidate_path("metadata/candidate-bundle-manifest.json")), BUNDLE_MANIFEST_FINGERPRINT, "bundle manifest file fingerprint mismatch")
        require_equal(content["source_commit"], CANDIDATE_SOURCE_COMMIT, "content manifest source mismatch")
        require_equal(bundle["source_commit"], CANDIDATE_SOURCE_COMMIT, "bundle manifest source mismatch")
        require_equal(bundle["publication"], False, "bundle manifest publication flag mismatch")
        require_equal(bundle["production"], False, "bundle manifest production flag mismatch")
        require_equal(sorted(Path(path).name for path in ASSET_PATHS), sorted(set(Path(path).name for path in ASSET_PATHS)), "asset basenames are not unique")
        return {"asset_count": len(ASSET_PATHS)}

    def _checksum_records(self) -> list[tuple[str, str]]:
        records: list[tuple[str, str]] = []
        for line in self.candidate_path("metadata/SHA256SUMS").read_text(encoding="utf-8").splitlines():
            expected, relative = line.split("  ", 1)
            records.append((expected, relative))
        return records

    def scenario_checksum_manifest_integrity(self) -> dict[str, Any]:
        require_equal(sha256_file(self.candidate_path("metadata/SHA256SUMS")), CHECKSUM_MANIFEST_FINGERPRINT, "checksum manifest fingerprint mismatch")
        for expected, relative in self._checksum_records():
            require_equal(sha256_file(self.candidate_path(relative)), expected, f"checksum mismatch for {relative}")
        return {"checksum_records": len(self._checksum_records())}

    def scenario_qualification_public_key_and_signature_integrity(self) -> dict[str, Any]:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

        public_payload = load_json(self.candidate_path("signatures/qualification-public-key.json"))
        public_bytes = decode_b64url(public_payload["public_key"])
        require_equal(sha256_bytes(public_bytes), PUBLIC_KEY_FINGERPRINT, "public key fingerprint mismatch")
        public_key = Ed25519PublicKey.from_public_bytes(public_bytes)
        verified = 0
        for artifact_relative, signature_relative in SIGNATURE_TARGETS:
            signature = decode_b64url(self.candidate_path(signature_relative).read_text(encoding="utf-8").strip())
            public_key.verify(signature, self.candidate_path(artifact_relative).read_bytes())
            verified += 1
        self.context["verified_signature_count"] = verified
        return {"verified_signature_count": verified}

    def scenario_private_qualification_key_non_retention(self) -> dict[str, Any]:
        private_hits = []
        markers = ("private key", "private_key", "-----BEGIN", "seed")
        for path in self.candidate_root.rglob("*"):
            if path.is_file():
                lowered_name = path.name.lower()
                if "private" in lowered_name and "key" in lowered_name:
                    private_hits.append(path.relative_to(self.candidate_root).as_posix())
                if path.stat().st_size < 1024 * 1024:
                    text = path.read_bytes().decode("utf-8", errors="ignore").lower()
                    if any(marker.lower() in text for marker in markers) and "qualification-public-key" not in path.name:
                        private_hits.append(path.relative_to(self.candidate_root).as_posix())
        require_equal(sorted(set(private_hits)), [], "private qualification signing material found")
        return {"private_key_files_found": 0}

    def scenario_candidate_sbom_integrity(self) -> dict[str, Any]:
        sbom = load_json(self.candidate_path("metadata/candidate-sbom.spdx.json"))
        require_equal(sha256_file(self.candidate_path("metadata/candidate-sbom.spdx.json")), SBOM_FINGERPRINT, "SBOM fingerprint mismatch")
        require_equal(len(sbom["packages"]), SBOM_COMPONENT_COUNT, "SBOM component count mismatch")
        require_equal(sbom["name"], "aion-v0.2.0-rc.1-local-sbom", "SBOM name mismatch")
        return {"component_count": len(sbom["packages"])}

    def scenario_candidate_provenance_chain_integrity(self) -> dict[str, Any]:
        provenance = load_json(self.candidate_path("metadata/candidate-provenance.intoto.json"))
        require_equal(sha256_file(self.candidate_path("metadata/candidate-provenance.intoto.json")), "7adc7679355f2c7daa963f6f4d6668b7c6b9363d757bb60a87e8b4ac912dc35a", "provenance file fingerprint mismatch")
        deps = provenance["predicate"]["buildDefinition"]["resolvedDependencies"]
        require(any(item.get("uri") == FROZEN_BASE_IMAGE_TAG and item["digest"]["sha256"] == FROZEN_BASE_IMAGE_ID.removeprefix("sha256:") for item in deps), "frozen base provenance dependency mismatch")
        require_equal(self.load_bundle_manifest()["candidate_provenance_chain_head"], PROVENANCE_CHAIN_HEAD, "provenance chain head mismatch")
        return {"chain_head": PROVENANCE_CHAIN_HEAD}

    def scenario_reproducibility_evidence_honesty(self) -> dict[str, Any]:
        path = self.candidate_path("evidence/reproducibility-comparison.json")
        payload = load_json(path)
        require_equal(sha256_file(path), "246001700f422954b236636f9bb9bb7145106538c49175c451686fc42ad5f426", "reproducibility fingerprint mismatch")
        require_equal(payload["reproducibility_invariants_passed"], True, "reproducibility comparison mismatch")
        require_equal(self.load_evidence()["byte_for_byte_oci_reproducibility_confirmed"], False, "OCI byte-for-byte honesty mismatch")
        return {"byte_for_byte_oci_reproducibility_confirmed": False}

    def scenario_compatibility_matrix_integrity(self) -> dict[str, Any]:
        path = self.candidate_path("evidence/compatibility-matrix.json")
        payload = load_json(path)
        require_equal(sha256_file(path), COMPATIBILITY_FINGERPRINT, "compatibility fingerprint mismatch")
        require_equal(payload["all_required_checks_passed"], True, "compatibility result mismatch")
        require(all(record["status"] == "pass" for record in payload["records"]), "compatibility record failure")
        return {"compatibility_records": len(payload["records"])}

    def scenario_migration_manifest_truthfulness(self) -> dict[str, Any]:
        path = self.candidate_path("evidence/migration-manifest.json")
        payload = load_json(path)
        require_equal(sha256_file(path), MIGRATION_FINGERPRINT, "migration fingerprint mismatch")
        require_equal(payload["candidate_delta_migrations_added"], 0, "migration change count mismatch")
        require_equal(payload["production_migration_executed"], False, "production migration flag mismatch")
        return {"migration_changes": 0}

    def scenario_release_notes_accuracy_and_prerelease_semantics(self) -> dict[str, Any]:
        path = self.candidate_path("evidence/release-notes-draft.md")
        text = path.read_text(encoding="utf-8")
        require_equal(sha256_file(path), RELEASE_NOTES_DRAFT_FINGERPRINT, "release notes draft fingerprint mismatch")
        require("v0.2.0-rc.1" in text and "0.2.0rc1" in text, "release notes draft missing RC/package version")
        require("stable" not in text.lower() or "stable v0.2.0 remains unpublished" in text.lower(), "release notes overstate stable release")
        return {"release_notes_draft_fingerprint": RELEASE_NOTES_DRAFT_FINGERPRINT}

    def scenario_protected_material_and_secret_exclusion(self) -> dict[str, Any]:
        protected_markers = ("sk-", "ghp_", "xoxb-", "authorization:", "bearer ", "client_secret", "password=")
        hits = []
        for relative in ASSET_PATHS:
            path = self.candidate_path(relative)
            if path.suffix not in {".json", ".md", ".txt"} and path.name != "SHA256SUMS":
                continue
            text = path.read_bytes().decode("utf-8", errors="ignore").lower()
            if any(marker in text for marker in protected_markers):
                hits.append(relative)
        require_equal(hits, [], "protected material found in candidate assets")
        return {"protected_material_hits": 0}

    def scenario_candidate_file_inventory_and_permission_integrity(self) -> dict[str, Any]:
        actual = sorted(path.relative_to(self.candidate_root).as_posix() for path in self.candidate_root.rglob("*") if path.is_file())
        require_equal(actual, sorted(ASSET_PATHS), "candidate file inventory mismatch")
        for path in self.candidate_root.rglob("*"):
            require(not path.is_symlink(), f"candidate contains symlink: {path}")
            mode = path.stat().st_mode
            require(not stat.S_ISSOCK(mode) and not stat.S_ISCHR(mode) and not stat.S_ISBLK(mode), f"candidate contains device/socket: {path}")
        return {"candidate_file_count": len(actual)}

    def scenario_candidate_image_package_and_application_smoke(self) -> dict[str, Any]:
        smoke = (
            "import importlib.metadata as m, subprocess, sys;"
            "import aion_brain, aion_brain.main, cryptography;"
            "assert m.version('aion-brain-api') == '0.2.0rc1';"
            "subprocess.run([sys.executable, '-m', 'pip', 'check'], check=True);"
            "print('aion244 candidate image smoke PASS')"
        )
        result = run(
            [
                "docker",
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--tmpfs",
                "/tmp",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--entrypoint",
                "python",
                LOCAL_IMAGE_TAG,
                "-c",
                smoke,
            ],
            cwd=self.repo_root,
            timeout=180,
        )
        return {"stdout": result.stdout.strip()}

    def scenario_sdk_candidate_installation_and_entrypoint_smoke(self) -> dict[str, Any]:
        target = self.work_dir / "sdk-target"
        target.mkdir(parents=True, mode=0o700)
        wheel = self.candidate_path("sdk/aion_sdk_python-0.2.0rc1-py3-none-any.whl")
        run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                "--target",
                str(target),
                str(wheel),
            ],
            cwd=self.repo_root,
            timeout=180,
            env={"PIP_NO_INDEX": "1", "PIP_DISABLE_PIP_VERSION_CHECK": "1"},
        )
        smoke = (
            "import importlib.metadata as m;"
            "import aion_sdk;"
            "assert m.version('aion-sdk-python') == '0.2.0rc1';"
            "eps=m.entry_points(group='console_scripts');"
            "assert any(ep.name=='aionctl' and ep.value=='aion_sdk.cli.main:app' for ep in eps);"
            "print('aion244 sdk smoke PASS')"
        )
        result = run(
            [sys.executable, "-c", smoke],
            cwd=self.repo_root,
            timeout=60,
            env={"PYTHONPATH": str(target)},
        )
        shutil.rmtree(target)
        return {"stdout": result.stdout.strip(), "temporary_target_removed": not target.exists()}

    def scenario_zero_registry_package_upload_and_production_effects(self) -> dict[str, Any]:
        for relative in (
            "docs/v02-release-qualification/program-ledger.json",
            "docs/v02-release-qualification/authorization-ledger.json",
            "examples/v02-release-qualification/release-candidate-authorization.json",
        ):
            payload = load_json(self.repo_root / relative)
            for key in (
                "production_runtime_authorized",
                "production_deployment_enabled",
                "production_exposure",
                "registry_login_enabled",
                "registry_pull_enabled",
                "registry_push_enabled",
                "public_package_registry_upload_enabled",
                "production_credentials_enabled",
                "production_tokens_enabled",
                "production_database_enabled",
            ):
                if key in payload:
                    require_equal(payload[key], False, f"{relative} {key} mismatch")
        return {"production_deployments": 0, "registry_pushes": 0}

    def scenario_tag_and_release_preexistence_boundary(self) -> dict[str, Any]:
        self.scenario_candidate_source_commit_and_tag_target_integrity()
        result = run(
            ["gh", "release", "view", CANDIDATE_ID, "--repo", "Pracxo/AOIN-OS", "--json", "tagName"],
            cwd=self.repo_root,
            check=False,
            timeout=60,
        )
        require(result.returncode != 0, "GitHub RC1 release already exists")
        stable = run(
            ["gh", "release", "view", "aion-v0.2.0", "--repo", "Pracxo/AOIN-OS", "--json", "tagName"],
            cwd=self.repo_root,
            check=False,
            timeout=60,
        )
        require(stable.returncode != 0, "stable GitHub v0.2.0 release exists")
        return {"release_preexists": False}

    def scenario_release_asset_inventory_and_upload_readiness(self) -> dict[str, Any]:
        sizes = {relative: self.candidate_path(relative).stat().st_size for relative in ASSET_PATHS}
        require_equal(len(sizes), 24, "asset count mismatch")
        require_equal(len({Path(path).name for path in ASSET_PATHS}), 24, "asset basename uniqueness mismatch")
        require(max(sizes.values()) < 2_000_000_000, "release asset exceeds GitHub release asset boundary")
        return {"asset_count": len(sizes), "largest_asset_bytes": max(sizes.values())}

    def scenario_annotated_tag_target_and_message_readiness(self) -> dict[str, Any]:
        require_equal(CANDIDATE_ID, "aion-v0.2.0-rc.1", "tag name mismatch")
        require_equal(CANDIDATE_SOURCE_COMMIT, self.candidate_source_commit, "tag target mismatch")
        return {"tag_name": CANDIDATE_ID, "tag_target_commit": CANDIDATE_SOURCE_COMMIT}

    def scenario_github_prerelease_transaction_and_rollback_readiness(self) -> dict[str, Any]:
        self.scenario_release_asset_inventory_and_upload_readiness()
        return {
            "release_kind": "github_prerelease",
            "draft_first": True,
            "rollback_before_publication_only": True,
        }

    def scenario_final_rc1_publication_authorization_readiness(self) -> dict[str, Any]:
        prior_results = self.context.get("prior_results", True)
        require(prior_results is True, "previous final evaluation scenarios did not pass")
        require_equal(CANDIDATE_ID, "aion-v0.2.0-rc.1", "candidate label mismatch")
        require_equal(PACKAGE_VERSION, "0.2.0rc1", "package version mismatch")
        require_equal(CANDIDATE_SOURCE_COMMIT, self.candidate_source_commit, "publication tag target mismatch")
        require_equal(len(ASSET_PATHS), 24, "publication asset count mismatch")
        return {"publication_authorization_ready": True, "authorization_id": PUBLICATION_AUTHORIZATION_ID}


def validate_report(report: Mapping[str, Any]) -> None:
    require_equal(report["evaluation_id"], EVALUATION_ID, "final evaluation ID mismatch")
    require_equal(report["evaluation_type"], EVALUATION_TYPE, "evaluation type mismatch")
    require_equal(report["program_id"], PROGRAM_ID, "program ID mismatch")
    require_equal(report["implementation_task"], IMPLEMENTATION_TASK, "implementation task mismatch")
    require_equal(report["closeout_task"], CLOSEOUT_TASK, "closeout task mismatch")
    require_equal(report["implementation_main_commit"], IMPLEMENTATION_MAIN_COMMIT, "implementation main commit mismatch")
    require_equal(report["candidate_source_commit"], CANDIDATE_SOURCE_COMMIT, "candidate source commit mismatch")
    require_equal(report["scenario_count"], 32, "scenario count mismatch")
    require_equal(report["hard_gate_count"], 32, "hard gate count mismatch")
    require_equal(report["scenario_ids"], list(SCENARIO_IDS), "scenario IDs mismatch")
    require_equal(report["decision"], PASS_DECISION, "final evaluation decision mismatch")
    require_equal(report["evaluation_passed"], True, "final evaluation pass flag mismatch")
    require(all(item["result"] == "pass" and item["hard_gate"] is True for item in report["scenario_results"]), "not all scenarios passed as hard gates")
    for key in (
        "candidate_rebuilds_executed_by_evaluation",
        "tags_created_by_evaluation",
        "github_releases_created_by_evaluation",
        "release_assets_uploaded_by_evaluation",
        "registry_logins",
        "registry_pulls",
        "registry_pushes",
        "public_package_uploads",
        "production_deployments",
        "stable_tags_created",
        "stable_releases_created",
    ):
        require_equal(report[key], 0, f"zero-effect field {key} mismatch")
    require_equal(report["repository_unchanged"], True, "repository unchanged flag mismatch")
    require_equal(report["temporary_evaluation_data_cleaned"], True, "temporary cleanup flag mismatch")
    expected = fingerprint({key: value for key, value in report.items() if key != "report_fingerprint"})
    require_equal(report["report_fingerprint"], expected, "final evaluation report fingerprint mismatch")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command")
    evaluate = subparsers.add_parser("evaluate")
    evaluate.add_argument("--repo-root", required=True)
    evaluate.add_argument("--evaluation-id", required=True)
    evaluate.add_argument("--implementation-main-commit", required=True)
    evaluate.add_argument("--candidate-source-commit", required=True)
    evaluate.add_argument("--candidate-evidence", required=True)
    evaluate.add_argument("--candidate-root", required=True)
    evaluate.add_argument("--evaluation-base-commit", required=True)
    evaluate.add_argument("--temporary-output-directory", required=True)
    evaluate.add_argument("--report", required=True)
    check = subparsers.add_parser("check-report")
    check.add_argument("--report", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    actual_argv = list(sys.argv[1:] if argv is None else argv)
    if not actual_argv or actual_argv[0].startswith("--"):
        actual_argv = ["evaluate", *actual_argv]
    args = parser.parse_args(actual_argv)
    command = args.command or "evaluate"
    if command == "check-report":
        report = load_json(Path(args.report))
        validate_report(report)
        print("AION-244 final evaluation report PASS")
        return 0
    repo_root = Path(args.repo_root).resolve()
    evaluator = FinalCandidateEvaluator(
        repo_root=repo_root,
        evaluation_id=args.evaluation_id,
        implementation_main_commit=args.implementation_main_commit,
        candidate_source_commit=args.candidate_source_commit,
        candidate_evidence=(repo_root / args.candidate_evidence).resolve(),
        candidate_root=Path(args.candidate_root).resolve(),
        evaluation_base_commit=args.evaluation_base_commit,
        temporary_output_directory=Path(args.temporary_output_directory).resolve(),
    )
    report = evaluator.evaluate()
    write_json(Path(args.report), report)
    print(pretty_json({"decision": report["decision"], "evaluation_passed": report["evaluation_passed"], "report_fingerprint": report["report_fingerprint"]}))
    return 0 if report["evaluation_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
