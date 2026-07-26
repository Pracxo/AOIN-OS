#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

"$PYTHON_BIN" - <<'PYSCRIPT'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
PROGRAM_ID = "AION-KNOWLEDGE-INTELLIGENCE-001"
AUTH_ID = "AION-210-KI-0004"
NEXT_AUTH_ID = "AION-212-KI-0005"
SUCCESSOR_AUTH_ID = "AION-214-KI-0006"
SCOPE = (
    "deterministic-evidence-corroboration-contradiction-freshness-source-"
    "independence-confidence-assessment-core"
)
NEXT_SCOPE = (
    "deterministic-domain-taxonomy-expert-profile-routing-independent-analysis-"
    "deliberation-disagreement-synthesis-abstention-core"
)
SUCCESSOR_SCOPE = (
    "deterministic-tool-manifest-intent-plan-simulation-verification-"
    "attestation-effect-evidence-rollback-abstention-core"
)
PROGRAM_STATE = "epistemic_truth_engine_implemented_persistent_write_disabled_pending_closeout"
POST_AION212_PROGRAM_STATES = {
    "domain_expert_mesh_authorized_not_implemented",
    "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout",
    "tool_verification_fabric_authorized_not_implemented",
}
ENGINE_STATE = "implemented_deterministic_in_memory_assessment_persistent_write_disabled"
SOURCE_FILES = {
    "services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
}
PROHIBITED_SOURCE_FILES = {
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/absolute_truth.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/knowledge_promotion.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/belief_mutation.py",
    "services/brain-api/src/aion_brain/api/epistemic_assessment.py",
}
REQUIRED_DOCS = {
    "docs/knowledge-intelligence/epistemic-assessment-implementation.md",
    "docs/knowledge-intelligence/epistemic-assessment-contracts.md",
    "docs/knowledge-intelligence/epistemic-assessment-request-model.md",
    "docs/knowledge-intelligence/epistemic-source-quality-metadata.md",
    "docs/knowledge-intelligence/epistemic-source-independence.md",
    "docs/knowledge-intelligence/epistemic-support-and-opposition.md",
    "docs/knowledge-intelligence/epistemic-freshness-evaluation.md",
    "docs/knowledge-intelligence/epistemic-scope-applicability.md",
    "docs/knowledge-intelligence/epistemic-relation-evaluation.md",
    "docs/knowledge-intelligence/epistemic-contradiction-evaluation.md",
    "docs/knowledge-intelligence/epistemic-scorecard-v1.md",
    "docs/knowledge-intelligence/epistemic-hard-caps.md",
    "docs/knowledge-intelligence/epistemic-confidence-bands.md",
    "docs/knowledge-intelligence/epistemic-abstention.md",
    "docs/knowledge-intelligence/epistemic-assessment-integrity.md",
    "docs/knowledge-intelligence/epistemic-assessment-fixture-replay.md",
    "docs/knowledge-intelligence/epistemic-assessment-security-review.md",
    "docs/knowledge-intelligence/epistemic-assessment-operator-runbook.md",
    "docs/knowledge-intelligence/aion-211-checklist.md",
    "docs/release/knowledge-intelligence-epistemic-assessment-implementation.md",
    "docs/release/knowledge-intelligence-epistemic-assessment-security-evidence.md",
    "docs/release/knowledge-intelligence-epistemic-assessment-runtime-hold.md",
    "docs/release/knowledge-intelligence-epistemic-assessment-no-go.md",
    "docs/release/knowledge-intelligence-epistemic-assessment-checklist.md",
    "docs/release/knowledge-intelligence-epistemic-assessment-evidence-matrix.md",
    "docs/adr/0175-deterministic-epistemic-evidence-assessment-engine-core.md",
}
REQUIRED_EXAMPLES = {
    "examples/knowledge-intelligence/epistemic-assessment-request.json",
    "examples/knowledge-intelligence/epistemic-freshness-policy.json",
    "examples/knowledge-intelligence/evidence-contribution.json",
    "examples/knowledge-intelligence/role-evidence-score.json",
    "examples/knowledge-intelligence/epistemic-scorecard-v1.json",
    "examples/knowledge-intelligence/epistemic-hard-cap-application.json",
    "examples/knowledge-intelligence/claim-epistemic-assessment.json",
    "examples/knowledge-intelligence/epistemic-assessment-batch.json",
    "examples/knowledge-intelligence/epistemic-assessment-query.json",
    "examples/knowledge-intelligence/epistemic-assessment-query-result.json",
    "examples/knowledge-intelligence/epistemic-assessment-integrity-report.json",
    "examples/knowledge-intelligence/epistemic-assessment-fixture-replay.json",
    "examples/knowledge-intelligence/epistemic-incident.json",
    "examples/knowledge-intelligence/epistemic-operator-review.json",
    "examples/knowledge-intelligence/epistemic-assessment-runtime-hold.json",
}
REQUIRED_STATIC = {
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-assessment.json",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-scorecard.json",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-hard-caps.json",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-integrity.json",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-runtime-hold.json",
}
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/architecture.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/visual-brain.md",
    "docs/adr/README.md",
    "docs/knowledge-intelligence/program-charter.md",
    "docs/knowledge-intelligence/architecture-roadmap.md",
    "docs/knowledge-intelligence/security-boundary.md",
    "docs/knowledge-intelligence/operator-model.md",
    "docs/knowledge-intelligence/program-ledger.json",
    "docs/knowledge-intelligence/authorization-ledger.json",
    "docs/knowledge-intelligence/epistemic-truth-engine-architecture.md",
    "docs/knowledge-intelligence/epistemic-truth-engine-boundary.md",
    "docs/knowledge-intelligence/epistemic-assessment-data-model.md",
    "docs/knowledge-intelligence/epistemic-corroboration-model.md",
    "docs/knowledge-intelligence/epistemic-contradiction-model.md",
    "docs/knowledge-intelligence/epistemic-freshness-model.md",
    "docs/knowledge-intelligence/epistemic-confidence-scorecard.md",
    "docs/knowledge-intelligence/epistemic-abstention-policy.md",
    "docs/knowledge-intelligence/epistemic-resource-budgets.md",
    "docs/knowledge-intelligence/epistemic-threat-model.md",
    "docs/knowledge-intelligence/epistemic-truth-engine-roadmap.md",
    "docs/release/knowledge-intelligence-epistemic-truth-authorization-transaction.md",
    "docs/release/knowledge-intelligence-epistemic-truth-scope.md",
    "docs/release/knowledge-intelligence-epistemic-truth-runtime-hold.md",
    "docs/release/knowledge-intelligence-epistemic-truth-checklist.md",
    "docs/release/v02-release-readiness-delta.md",
    "examples/knowledge-intelligence/epistemic-truth-authorization.json",
    "examples/knowledge-intelligence/epistemic-runtime-hold.json",
    "operator-console-static/index.html",
    "operator-console-static/app.js",
    "operator-console-static/README.md",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-truth-authorization.json",
	    "operator-console-static/demo-data/knowledge-intelligence-epistemic-runtime-hold.json",
	    "services/brain-api/tests/knowledge_claim_graph_evaluation_test_helpers.py",
	    "services/brain-api/tests/test_knowledge_claim_graph_authorization_validator.py",
	    "services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py",
	    "services/brain-api/tests/test_knowledge_research_authorization_closeout.py",
	    "services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py",
	    "scripts/connector-runtime-no-external-call-regression.sh",
	    "scripts/knowledge-intelligence-claim-graph-authorization-check.sh",
    "scripts/knowledge-intelligence-epistemic-truth-authorization-check.sh",
    "scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh",
    "scripts/knowledge-intelligence-epistemic-assessment-check.sh",
    "scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh",
    "scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-claim-graph-runtime-hold.sh",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-runtime-hold.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-runtime-hold.sh",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/operator-action-write-path-no-go-regression.sh",
    "scripts/operator-console-static-check.sh",
    "scripts/production-auth-architecture-check.sh",
    "scripts/production-auth-core-no-go-regression.sh",
    "scripts/static-console-safety-check.sh",
}
ALLOWED_PREFIXES = (
    "services/brain-api/tests/test_knowledge_epistemic_assessment_",
)
AION212_ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/epistemic-assessment-operator-evaluation",
    "docs/knowledge-intelligence/epistemic-assessment-evaluation",
    "docs/knowledge-intelligence/domain-expert-mesh",
    "docs/knowledge-intelligence/domain-taxonomy",
    "docs/knowledge-intelligence/domain-expert-",
    "docs/release/knowledge-intelligence-epistemic-assessment-evaluation",
    "docs/release/knowledge-intelligence-domain-expert-mesh",
    "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation",
    "examples/knowledge-intelligence/epistemic-assessment-evaluation",
    "examples/knowledge-intelligence/domain-expert-mesh",
    "examples/knowledge-intelligence/domain-taxonomy",
    "examples/knowledge-intelligence/domain-expert-",
    "examples/knowledge-intelligence/expert-",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-assessment-evaluation",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-",
    "scripts/knowledge-intelligence-epistemic-assessment-operator-evaluation",
    "scripts/knowledge-intelligence-domain-expert-mesh",
    "scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py",
    "scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py",
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_",
    "services/brain-api/tests/test_knowledge_epistemic_assessment_operator_evaluation",
    "services/brain-api/tests/test_knowledge_domain_expert_mesh_",
)
AION212_ALLOWED_EXACT = {
    "docs/adr/0176-epistemic-assessment-evaluation-and-domain-expert-mesh-authorization.md",
    "docs/adr/0177-deterministic-domain-expert-mesh-core.md",
    "docs/knowledge-intelligence/aion-213-checklist.md",
    "docs/knowledge-intelligence/computational-expert-profiles.md",
    "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json",
    "examples/knowledge-intelligence/epistemic-assessment-evaluation-scenario-summary.json",
    "scripts/auth-design-check.sh",
    "scripts/knowledge-intelligence-claim-graph-authorization-check.sh",
    "scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-check.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/lib/v02_production_auth_authorization.py",
    "services/brain-api/tests/knowledge_claim_graph_evaluation_test_helpers.py",
    "services/brain-api/tests/knowledge_domain_expert_mesh_test_helpers.py",
    "services/brain-api/tests/knowledge_source_registry_test_helpers.py",
    "services/brain-api/tests/test_knowledge_claim_graph_authorization_closeout.py",
    "services/brain-api/tests/test_knowledge_claim_graph_authorization_validator.py",
    "services/brain-api/tests/test_knowledge_epistemic_truth_authorization_validator.py",
    "services/brain-api/tests/test_knowledge_intelligence_current_projection.py",
    "services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py",
    "services/brain-api/tests/test_knowledge_research_authorization_closeout.py",
    "services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py",
}
AION214_ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/domain-expert-mesh-operator-evaluation",
    "docs/knowledge-intelligence/domain-expert-mesh-evaluation",
    "docs/knowledge-intelligence/tool-",
    "docs/release/knowledge-intelligence-domain-expert-mesh-operator-evaluation",
    "docs/release/knowledge-intelligence-tool-verification",
    "examples/knowledge-intelligence/domain-expert-mesh-operator-evaluation",
    "examples/knowledge-intelligence/tool-",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-operator-evaluation",
    "operator-console-static/demo-data/knowledge-intelligence-tool-",
    "scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation",
    "scripts/knowledge-intelligence-tool-verification",
    "services/brain-api/tests/test_knowledge_domain_expert_mesh_operator_evaluation",
    "services/brain-api/tests/test_knowledge_tool_verification",
)
AION214_ALLOWED_EXACT = {
    "docs/adr/0178-domain-expert-mesh-evaluation-and-tool-verification-authorization.md",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh",
    "scripts/lib/knowledge_intelligence_domain_expert_mesh_operator_evaluation.py",
    "scripts/lib/knowledge_intelligence_tool_verification_authorization.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "packages/aion-sdk-python/src/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
    "services/brain-api/src/aion_brain/self_improvement/",
    "services/brain-api/src/aion_brain/production_auth/",
    "services/brain-api/src/aion_brain/kernel/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/api_support/",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/security/",
)
PROHIBITED_EXACT = {
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
}
FALSE_FLAGS = {
    "epistemic_truth_engine_runtime_enabled",
    "persistent_assessment_write_enabled",
    "assessment_database_enabled",
    "absolute_truth_oracle_enabled",
    "claim_true_boolean_assignment_enabled",
    "claim_false_boolean_assignment_enabled",
    "automatic_claim_acceptance_enabled",
    "automatic_claim_rejection_enabled",
    "automatic_claim_extraction_enabled",
    "automatic_correction_effect_enabled",
    "automatic_retraction_effect_enabled",
    "automatic_supersession_effect_enabled",
    "contradiction_resolution_enabled",
    "knowledge_promotion_enabled",
    "verified_knowledge_creation_enabled",
    "automatic_memory_ingestion_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "network_access_enabled",
    "public_network_fetch_enabled",
    "runtime_effect",
}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def git_ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = ["origin/main", "main"]
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
    for candidate in candidates:
        if not git_ref_exists(candidate):
            continue
        merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    return "HEAD~1" if git_ref_exists("HEAD~1") else None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base is not None:
        output = run(["git", "diff", "--name-status", base, "HEAD"]).stdout
        entries.extend(line.split("\t") for line in output.splitlines() if line.strip())
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def allowed_path(path: str) -> bool:
    if path in ALLOWED_EXACT or path in SOURCE_FILES or path in REQUIRED_DOCS:
        return True
    if path in REQUIRED_EXAMPLES or path in REQUIRED_STATIC:
        return True
    if path in AION212_ALLOWED_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in AION212_ALLOWED_PREFIXES):
        return True
    if path in AION214_ALLOWED_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in AION214_ALLOWED_PREFIXES):
        return True
    return any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES)


def assert_changed_paths() -> None:
    for parts in changed_entries():
        status, paths = parts[0], parts[1:]
        if status.startswith(("D", "R")):
            raise SystemExit(f"deletion or rename is not allowed for AION-211: {parts}")
        for path in paths:
            normalized = path.replace("\\", "/")
            if normalized in PROHIBITED_EXACT or Path(normalized).name in PROHIBITED_EXACT:
                raise SystemExit(f"prohibited exact path changed: {normalized}")
            if normalized.startswith(PROHIBITED_PREFIXES):
                raise SystemExit(f"prohibited runtime or governance path changed: {normalized}")
            if (
                normalized.startswith("services/brain-api/src/aion_brain/")
                and normalized not in SOURCE_FILES
                and not allowed_path(normalized)
            ):
                raise SystemExit(f"source path outside exact AION-211 scope changed: {normalized}")
            if not allowed_path(normalized):
                raise SystemExit(f"path outside AION-211 scope changed: {normalized}")


def assert_required_files() -> None:
    for relative in sorted(SOURCE_FILES | REQUIRED_DOCS | REQUIRED_EXAMPLES | REQUIRED_STATIC):
        if not (ROOT / relative).is_file():
            raise SystemExit(f"required AION-211 file missing: {relative}")
    for relative in sorted(PROHIBITED_SOURCE_FILES):
        if (ROOT / relative).exists():
            raise SystemExit(f"prohibited AION-211 runtime file exists: {relative}")
    adr_index = (ROOT / "docs/adr/README.md").read_text(encoding="utf-8")
    if "0175-deterministic-epistemic-evidence-assessment-engine-core.md" not in adr_index:
        raise SystemExit("ADR 0175 is not indexed")


def assert_json_evidence() -> None:
    for relative in sorted(REQUIRED_EXAMPLES | REQUIRED_STATIC):
        payload = load_json(relative)
        for key, expected in {
            "program_id": PROGRAM_ID,
            "authorization_transaction_id": AUTH_ID,
            "implementation_task": "AION-211",
            "formal_closeout_task": "AION-212",
            "authorization_scope": SCOPE,
            "epistemic_truth_engine_authorized": True,
            "epistemic_truth_engine_implemented": True,
            "epistemic_truth_engine_runtime_enabled": False,
            "persistent_assessment_write_enabled": False,
            "absolute_truth_oracle_enabled": False,
            "automatic_claim_acceptance_enabled": False,
            "automatic_claim_rejection_enabled": False,
            "knowledge_promotion_enabled": False,
            "belief_mutation_enabled": False,
            "runtime_effect": False,
            "synthetic": True,
            "read_only": True,
            "redacted": True,
        }.items():
            if payload.get(key) != expected:
                raise SystemExit(f"{relative} has invalid {key}: {payload.get(key)!r}")


def assert_ledgers() -> None:
    program = load_json("docs/knowledge-intelligence/program-ledger.json")
    auth = load_json("docs/knowledge-intelligence/authorization-ledger.json")
    post_aion212 = (ROOT / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json").exists()
    for label, payload in (("program", program), ("authorization", auth)):
        post_aion214 = payload.get("program_state") == "tool_verification_fabric_authorized_not_implemented"
        if payload["program_id"] != PROGRAM_ID:
            raise SystemExit(f"{label} ledger program mismatch")
        expected_states = POST_AION212_PROGRAM_STATES if post_aion212 else {PROGRAM_STATE}
        if payload["program_state"] not in expected_states:
            raise SystemExit(f"{label} ledger program_state mismatch")
        if payload["active_knowledge_implementation_authorization_count"] != 1:
            raise SystemExit(f"{label} ledger active authorization count mismatch")
        if post_aion214:
            if payload["active_knowledge_implementation_authorization"] != SUCCESSOR_AUTH_ID:
                raise SystemExit(f"{label} ledger active authorization mismatch")
            if payload["active_knowledge_implementation_task"] != "AION-215":
                raise SystemExit(f"{label} ledger active task mismatch")
            if payload["formal_closeout_task"] != "AION-216":
                raise SystemExit(f"{label} ledger closeout mismatch")
        elif post_aion212:
            if payload["active_knowledge_implementation_authorization"] != NEXT_AUTH_ID:
                raise SystemExit(f"{label} ledger active authorization mismatch")
            if payload["active_knowledge_implementation_task"] != "AION-213":
                raise SystemExit(f"{label} ledger active task mismatch")
            if payload["formal_closeout_task"] != "AION-214":
                raise SystemExit(f"{label} ledger closeout mismatch")
        else:
            if payload["active_knowledge_implementation_authorization"] != AUTH_ID:
                raise SystemExit(f"{label} ledger active authorization mismatch")
            if payload["active_knowledge_implementation_task"] != "AION-211":
                raise SystemExit(f"{label} ledger active task mismatch")
            if payload["formal_closeout_task"] != "AION-212":
                raise SystemExit(f"{label} ledger closeout mismatch")
        if payload["epistemic_truth_engine_authorized"] is not True:
            raise SystemExit(f"{label} ledger engine authorization missing")
        if payload["epistemic_truth_engine_implemented"] is not True:
            raise SystemExit(f"{label} ledger engine implementation missing")
        if payload["epistemic_truth_engine_state"] != ENGINE_STATE:
            raise SystemExit(f"{label} ledger engine state mismatch")
        expected_new_auth = True if post_aion212 else False
        if payload["new_knowledge_implementation_authorization_created"] is not expected_new_auth:
            raise SystemExit(f"{label} ledger new authorization flag mismatch")
        for key in FALSE_FLAGS:
            if payload.get(key, False) is not False:
                raise SystemExit(f"{label} ledger flag must remain false: {key}")

    records = auth["records"]
    active = [record for record in records if record.get("authorization_active") is True]
    if len(active) != 1:
        raise SystemExit("exactly one Knowledge Intelligence authorization must be active")
    active_record = active[0]
    post_aion214 = program.get("program_state") == "tool_verification_fabric_authorized_not_implemented"
    if post_aion214:
        expected_active = SUCCESSOR_AUTH_ID
        expected_scope = SUCCESSOR_SCOPE
        expected_task = "AION-215"
        expected_closeout = "AION-216"
    else:
        expected_active = NEXT_AUTH_ID if post_aion212 else AUTH_ID
        expected_scope = NEXT_SCOPE if post_aion212 else SCOPE
        expected_task = "AION-213" if post_aion212 else "AION-211"
        expected_closeout = "AION-214" if post_aion212 else "AION-212"
    if active_record["authorization_transaction_id"] != expected_active:
        raise SystemExit("active authorization mismatch")
    if active_record["approval_record_id"] != expected_active:
        raise SystemExit("active approval record mismatch")
    if active_record["implementation_task"] != expected_task:
        raise SystemExit("active authorization implementation task mismatch")
    if active_record["formal_closeout_task"] != expected_closeout:
        raise SystemExit("active authorization formal closeout mismatch")
    if active_record["authorization_scope"] != expected_scope:
        raise SystemExit("active authorization scope mismatch")
    if active_record["authorization_consumed"] or active_record["authorization_expired"] or active_record["authorization_reusable"]:
        raise SystemExit("active authorization must remain unconsumed, unexpired, and non-reusable")
    if post_aion214:
        if active_record["resource_limits"]["maximum_persistent_tool_state_write_batch"] != 0:
            raise SystemExit("persistent tool state write budget must remain zero")
    elif post_aion212:
        if active_record["resource_limits"]["maximum_persistent_mesh_write_batch"] != 0:
            raise SystemExit("persistent mesh write budget must remain zero")
    elif active_record["resource_limits"]["maximum_persistent_assessment_write_batch"] != 0:
        raise SystemExit("persistent assessment write budget must remain zero")
    if not post_aion214 and not active_record["epistemic_truth_engine_implemented"]:
        raise SystemExit("active authorization must record AION-211 implementation evidence")
    if active_record.get("epistemic_truth_engine_runtime_enabled", False):
        raise SystemExit("epistemic assessment runtime must remain disabled")
    closed = [
        record
        for record in records
        if record.get("authorization_transaction_id") == AUTH_ID
    ]
    if len(closed) != 1:
        raise SystemExit("AION-210-KI-0004 record missing")
    if post_aion212 and (
        closed[0]["authorization_active"] is not False
        or closed[0]["authorization_consumed"] is not True
        or closed[0]["authorization_expired"] is not True
        or closed[0]["authorization_reusable"] is not False
    ):
        raise SystemExit("AION-210-KI-0004 closeout lifecycle mismatch")
    for key, value in active_record.get("prohibited_capabilities", {}).items():
        if value is not False:
            raise SystemExit(f"prohibited capability must remain false: {key}")


def assert_no_persistence_files() -> None:
    output = run(["git", "ls-files"]).stdout
    blocked_suffixes = (".db", ".sqlite", ".sqlite3", ".jsonl", ".assessment", ".state")
    for relative in output.splitlines():
        if relative.endswith(blocked_suffixes):
            raise SystemExit(f"tracked assessment persistence file detected: {relative}")


assert_changed_paths()
assert_required_files()
assert_json_evidence()
assert_ledgers()
assert_no_persistence_files()
PYSCRIPT

source_paths=(
  services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py
  services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py
)

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|subprocess|git|github)([[:space:].]|$)' "${source_paths[@]}"; then
  echo "ERROR: prohibited network, database, runtime, or Git import" >&2
  exit 1
fi

if rg -n 'model_provider|llm|completion|embedding|learned_weight|hidden_weight|random[.]' "${source_paths[@]}"; then
  echo "ERROR: prohibited model call, random scoring, or hidden weighting" >&2
  exit 1
fi

if rg -n 'claim_true[[:space:]]*=[[:space:]]*true|claim_false[[:space:]]*=[[:space:]]*true|claim_accepted[[:space:]]*=[[:space:]]*true|claim_rejected[[:space:]]*=[[:space:]]*true|knowledge_promoted[[:space:]]*=[[:space:]]*true|belief_mutated[[:space:]]*=[[:space:]]*true|persistent_write_applied[[:space:]]*=[[:space:]]*true|runtime_effect[[:space:]]*=[[:space:]]*true' "${source_paths[@]}"; then
  echo "ERROR: prohibited truth, knowledge, belief, persistence, or runtime effect" >&2
  exit 1
fi

if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null

if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence epistemic assessment no-go PASS"
