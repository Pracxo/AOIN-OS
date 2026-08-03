#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_BRAIN_PYTHON="$PYTHON_BIN"

./scripts/v02-staging-qualification-no-go-regression.sh >/dev/null
./scripts/v02-staging-qualification-pilot-evidence-check.sh >/dev/null

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path

from aion_brain.contracts import v02_staging_qualification as c
from aion_brain.v02_staging_qualification import (
    ControlledV02StagingQualificationService,
)
import v02_release_qualification_foundation_operator_evaluation as aion240
import v02_staging_qualification_operator_evaluation as ev

root = Path.cwd()
required_docs = (
    "docs/v02-release-qualification/staging-qualification-implementation.md",
    "docs/v02-release-qualification/staging-qualification-contracts.md",
    "docs/v02-release-qualification/staging-qualification-component-lineage.md",
    "docs/v02-release-qualification/staging-qualification-session.md",
    "docs/v02-release-qualification/staging-docker-context-boundary.md",
    "docs/v02-release-qualification/staging-source-snapshot-implementation.md",
    "docs/v02-release-qualification/staging-offline-build-implementation.md",
    "docs/v02-release-qualification/staging-artifact-manifest-implementation.md",
    "docs/v02-release-qualification/staging-sbom-implementation.md",
    "docs/v02-release-qualification/staging-provenance-implementation.md",
    "docs/v02-release-qualification/staging-reproducibility-comparison.md",
    "docs/v02-release-qualification/staging-environment-implementation.md",
    "docs/v02-release-qualification/staging-identity-fixture.md",
    "docs/v02-release-qualification/staging-replay-fixture.md",
    "docs/v02-release-qualification/staging-deployment-implementation.md",
    "docs/v02-release-qualification/staging-health-readiness-implementation.md",
    "docs/v02-release-qualification/staging-security-validation-implementation.md",
    "docs/v02-release-qualification/staging-observability-implementation.md",
    "docs/v02-release-qualification/staging-rollback-implementation.md",
    "docs/v02-release-qualification/staging-cleanup-implementation.md",
    "docs/v02-release-qualification/staging-security-review.md",
    "docs/v02-release-qualification/staging-operator-runbook.md",
    "docs/v02-release-qualification/staging-pilot-report.md",
    "docs/v02-release-qualification/aion-241-checklist.md",
    "docs/release/v02-staging-qualification-implementation.md",
    "docs/release/v02-staging-qualification-security-evidence.md",
    "docs/release/v02-staging-qualification-pilot.md",
    "docs/release/v02-staging-qualification-runtime-hold.md",
    "docs/release/v02-staging-qualification-no-go.md",
    "docs/release/v02-staging-qualification-checklist.md",
    "docs/release/v02-staging-qualification-evidence-matrix.md",
    "docs/adr/0205-controlled-isolated-local-staging-artifact-build-and-rollback-drill.md",
)
for relative in required_docs:
    if not (root / relative).is_file():
        raise SystemExit(f"missing AION-241 documentation: {relative}")
if "0205-controlled-isolated-local-staging-artifact-build-and-rollback-drill.md" not in (
    root / "docs/adr/README.md"
).read_text(encoding="utf-8"):
    raise SystemExit("ADR 0205 is not indexed")

required_examples = (
    "examples/v02-release-qualification/staging-component-binding.json",
    "examples/v02-release-qualification/staging-authorization-envelope.json",
    "examples/v02-release-qualification/staging-session-plan.json",
    "examples/v02-release-qualification/staging-source-snapshot.json",
    "examples/v02-release-qualification/staging-docker-context-boundary.json",
    "examples/v02-release-qualification/staging-local-image-inventory.json",
    "examples/v02-release-qualification/staging-build-plan.json",
    "examples/v02-release-qualification/staging-artifact-manifest.json",
    "examples/v02-release-qualification/staging-sbom.json",
    "examples/v02-release-qualification/staging-provenance.json",
    "examples/v02-release-qualification/staging-reproducibility-comparison.json",
    "examples/v02-release-qualification/staging-environment-profile.json",
    "examples/v02-release-qualification/staging-identity-fixture.json",
    "examples/v02-release-qualification/staging-replay-fixture.json",
    "examples/v02-release-qualification/staging-deployment-plan.json",
    "examples/v02-release-qualification/staging-health-readiness.json",
    "examples/v02-release-qualification/staging-security-validation.json",
    "examples/v02-release-qualification/staging-observability.json",
    "examples/v02-release-qualification/staging-rollback-plan.json",
    "examples/v02-release-qualification/staging-cleanup-result.json",
    "examples/v02-release-qualification/staging-evidence-bundle-projection.json",
    "examples/v02-release-qualification/v02-controlled-isolated-staging-pilot-evidence.json",
)
for relative in required_examples:
    if not (root / relative).is_file():
        raise SystemExit(f"missing AION-241 example/evidence: {relative}")

program = json.loads((root / "docs/v02-release-qualification/program-ledger.json").read_text(encoding="utf-8"))
auth = json.loads((root / "docs/v02-release-qualification/authorization-ledger.json").read_text(encoding="utf-8"))
staging_auth = json.loads((root / "examples/v02-release-qualification/staging-qualification-authorization.json").read_text(encoding="utf-8"))
evidence = json.loads((root / "examples/v02-release-qualification/v02-controlled-isolated-staging-pilot-evidence.json").read_text(encoding="utf-8"))
aion243_evidence_exists = (
    root / "examples/v02-release-qualification/v02-release-candidate-artifact-build-evidence.json"
).is_file()
if auth.get("authorization_transaction_id") == ev.NEXT_AUTHORIZATION_ID:
    report = json.loads((root / "examples/v02-release-qualification/staging-qualification-operator-evaluation-report.json").read_text(encoding="utf-8"))
    ev.validate_report(report)
    if report["decision"] != ev.PASS_DECISION:
        raise SystemExit("AION-242 staging operator evaluation must pass")
    closeout = program.get("aion_240_authorization_closeout", {})
    if closeout.get("authorization_transaction_id") != ev.CURRENT_AUTHORIZATION_ID:
        raise SystemExit("AION-240 closeout record missing after AION-242")
    if closeout.get("authorization_active") is not False or closeout.get("authorization_consumed") is not True:
        raise SystemExit("AION-240 must be closed and consumed after AION-242")
    if closeout.get("authorization_expired") is not True or closeout.get("authorization_reusable") is not False:
        raise SystemExit("AION-240 must be expired and non-reusable after AION-242")
    record = program.get("aion_241_record", {})
    if record.get("ci_result") != "pass":
        raise SystemExit("AION-241 CI reconciliation mismatch after AION-242")
    if record.get("feature_commits") != [ev.IMPLEMENTATION_COMMIT, ev.EVIDENCE_COMMIT]:
        raise SystemExit("AION-241 feature commit reconciliation mismatch after AION-242")
    if record.get("pull_requests") != [ev.IMPLEMENTATION_PR]:
        raise SystemExit("AION-241 PR reconciliation mismatch after AION-242")
    if record.get("merge_commits") != [ev.IMPLEMENTATION_MERGE_COMMIT]:
        raise SystemExit("AION-241 merge reconciliation mismatch after AION-242")
    if record.get("pilot_report_fingerprint") != ev.EXPECTED_PILOT_FINGERPRINT:
        raise SystemExit("AION-241 pilot fingerprint mismatch after AION-242")
    for label, payload in (("program", program), ("authorization", auth)):
        if payload.get("active_v02_release_qualification_authorization") != ev.NEXT_AUTHORIZATION_ID:
            raise SystemExit(f"{label} active authorization mismatch after AION-242")
        if payload.get("active_v02_release_qualification_task") != ev.NEXT_IMPLEMENTATION_TASK:
            raise SystemExit(f"{label} active task mismatch after AION-242")
        if payload.get("release_candidate_artifact_build_authorized") is not True:
            raise SystemExit(f"{label} release-candidate authorization missing after AION-242")
        if aion243_evidence_exists:
            if payload.get("release_candidate_created") is not True:
                raise SystemExit(f"{label} AION-243 local release candidate state missing")
        elif payload.get("release_candidate_created") is not False:
            raise SystemExit(f"{label} release candidate must remain absent after AION-242")
        if payload.get("v02_release_ready") is not False:
            raise SystemExit(f"{label} v02_release_ready must remain false after AION-242")
    sys.exit(0)
if auth.get("active_v02_release_qualification_authorization") == "AION-244-V02REL-0001":
    for label, payload in (("program", program), ("authorization", auth)):
        closeout = payload.get("aion_242_authorization_closeout", {})
        publication_auth = payload.get("aion_244_publication_authorization", {})
        if closeout.get("authorization_transaction_id") != ev.NEXT_AUTHORIZATION_ID:
            raise SystemExit(f"{label} missing AION-242 authorization closeout after AION-244")
        if closeout.get("authorization_active") is not False or closeout.get("authorization_consumed") is not True:
            raise SystemExit(f"{label} AION-242 authorization closeout mismatch after AION-244")
        if publication_auth.get("authorization_transaction_id") != "AION-244-V02REL-0001":
            raise SystemExit(f"{label} missing AION-244 publication authorization")
        if publication_auth.get("authorization_active") is not True:
            raise SystemExit(f"{label} AION-244 publication authorization must be active")
        if publication_auth.get("authorization_consumed") is not False:
            raise SystemExit(f"{label} AION-244 publication authorization must be unconsumed")
        for key, expected in {
            "release_candidate_artifact_build_implemented": True,
            "release_candidate_created": True,
            "release_candidate_published": False,
            "release_candidate_creation_enabled": False,
            "v02_release_ready": False,
            "v02_tag_created": False,
            "v02_release_created": False,
            "production_runtime_authorized": False,
            "production_deployment_enabled": False,
        }.items():
            if payload.get(key) != expected:
                raise SystemExit(f"{label} AION-244 carried-forward staging mismatch {key}: {payload.get(key)!r}")
    sys.exit(0)
final_state = (
    "controlled_isolated_staging_qualification_implemented_pilot_complete_pending_closeout"
)
controlled_state = "implemented_isolated_local_pilot_complete_pending_AION-242_closeout"
for label, payload in (("program", program), ("authorization", auth)):
    required = {
        "program_id": c.PROGRAM_ID,
        "program_state": final_state,
        "v02_release_qualification_program_authorized": True,
        "v02_release_qualification_foundation_implemented": True,
        "v02_release_qualification_foundation_operator_evaluation_passed": True,
        "active_v02_release_qualification_authorization_count": 1,
        "active_v02_release_qualification_authorization": c.AUTHORIZATION_TRANSACTION_ID,
        "active_v02_release_qualification_task": c.IMPLEMENTATION_TASK,
        "formal_closeout_task": c.FORMAL_CLOSEOUT_TASK,
        "final_planned_task": c.FINAL_PLANNED_TASK,
        "controlled_staging_qualification_authorized": True,
        "controlled_staging_qualification_implemented": True,
        "controlled_staging_qualification_state": controlled_state,
        "local_staging_pilot_completed": True,
        "offline_local_build_completed": True,
        "local_staging_artifact_created": True,
        "local_sbom_created": True,
        "local_provenance_created": True,
        "isolated_staging_deployment_completed": True,
        "staging_security_validation_completed": True,
        "staging_rollback_drill_completed": True,
        "staging_cleanup_completed": True,
        "active_staging_resources": 0,
        "production_runtime_authorized": False,
        "production_deployment_enabled": False,
        "release_candidate_creation_enabled": False,
        "v02_release_ready": False,
        "v02_tag_created": False,
        "v02_release_created": False,
    }
    for key, expected in required.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{label} final-state mismatch {key}: {payload.get(key)!r}")
    if payload.get("resource_limits") != c.resource_limits().model_dump():
        raise SystemExit(f"{label} AION-241 resource limits mismatch")
    if payload.get("approved_capabilities") != {key: True for key in c.APPROVED_CAPABILITIES}:
        raise SystemExit(f"{label} AION-241 approved capabilities mismatch")
    if payload.get("prohibited_capabilities") != {key: False for key in c.PROHIBITED_CAPABILITIES}:
        raise SystemExit(f"{label} AION-241 prohibited capabilities mismatch")
    record = payload.get("aion_240_record", {})
    if record.get("ci_result") != "pass":
        raise SystemExit(f"{label} AION-240 CI reconciliation mismatch")
    if record.get("feature_commits") != [
        "45b50d79edc6080e2e64e0566dc17ead9bcf0090",
        "ab76a9fe4814e9a36a612cc768b343fd6117dcaa",
    ]:
        raise SystemExit(f"{label} AION-240 feature commits mismatch")
    if record.get("merge_commits") != ["9f6b899f84ef8d9a53598871dbbd5b0cb3bacb38"]:
        raise SystemExit(f"{label} AION-240 merge commit mismatch")
    if record.get("evaluation_report_fingerprint") != "6a9c94362fc9258db33ec41914080834b4af2811ac4b1d934ee43113779c72f4":
        raise SystemExit(f"{label} AION-240 report fingerprint mismatch")
    aion241 = payload.get("aion_241_record", {})
    if aion241.get("source_snapshot_commit") != evidence.get("implementation_commit"):
        raise SystemExit(f"{label} AION-241 source snapshot commit mismatch")
    if aion241.get("runtime_state") != final_state:
        raise SystemExit(f"{label} AION-241 runtime state mismatch")
    if aion241.get("authorization_state") != "implementation_complete_pending_AION-242_closeout":
        raise SystemExit(f"{label} AION-241 authorization state mismatch")

for key in (
    "authorization_transaction_id",
    "candidate_id",
    "workstream",
    "implementation_task",
    "formal_closeout_task",
    "final_planned_task",
    "authorization_scope",
):
    expected = {
        "authorization_transaction_id": c.AUTHORIZATION_TRANSACTION_ID,
        "candidate_id": c.CANDIDATE_ID,
        "workstream": c.WORKSTREAM,
        "implementation_task": c.IMPLEMENTATION_TASK,
        "formal_closeout_task": c.FORMAL_CLOSEOUT_TASK,
        "final_planned_task": c.FINAL_PLANNED_TASK,
        "authorization_scope": c.AUTHORIZATION_SCOPE,
    }[key]
    if staging_auth.get(key) != expected:
        raise SystemExit(f"staging authorization mismatch {key}: {staging_auth.get(key)!r}")

service = ControlledV02StagingQualificationService()
bundle = service.run_canonical_pilot_projection()
if bundle.pilot_id != c.PILOT_ID:
    raise SystemExit("service pilot projection mismatch")
if bundle.v02_release_ready is not False:
    raise SystemExit("service must preserve v02 release hold")
if sum(bundle.prohibited_effect_counters.values()) != 0:
    raise SystemExit("service produced prohibited effects")
if service.reject_changed_replay(bundle.pilot_id) is not True:
    raise SystemExit("service did not reject changed replay")

if aion240.NEXT_AUTHORIZATION_ID != c.AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-240/AION-241 authorization linkage mismatch")
PY

PYTHONPATH="$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_v02_staging_qualification_aion241.py \
  -q

./scripts/v02-staging-qualification-authorization-no-go-regression.sh >/dev/null
./scripts/v02-staging-qualification-authorization-check.sh >/dev/null
AION_AGGREGATE_GATE_RUNNING=1 AION_CHECK_RUNNING=1 ./scripts/v02-release-qualification-foundation-check.sh >/dev/null

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "controlled isolated staging qualification PASS"
