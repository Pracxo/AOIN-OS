#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/knowledge-intelligence-domain-expert-mesh-no-go-regression.sh
./scripts/knowledge-intelligence-domain-expert-mesh-authorization-check.sh

json_files=(
  examples/knowledge-intelligence/domain-taxonomy.json
  examples/knowledge-intelligence/domain-expert-profile.json
  examples/knowledge-intelligence/domain-expert-case.json
  examples/knowledge-intelligence/expert-subquestion-plan.json
  examples/knowledge-intelligence/expert-panel-plan.json
  examples/knowledge-intelligence/expert-perspective-report.json
  examples/knowledge-intelligence/expert-critique.json
  examples/knowledge-intelligence/expert-critique-response.json
  examples/knowledge-intelligence/expert-disagreement-matrix.json
  examples/knowledge-intelligence/expert-mesh-synthesis.json
  examples/knowledge-intelligence/domain-expert-mesh-session.json
  examples/knowledge-intelligence/domain-expert-mesh-query.json
  examples/knowledge-intelligence/domain-expert-mesh-query-result.json
  examples/knowledge-intelligence/domain-expert-mesh-integrity-report.json
  examples/knowledge-intelligence/domain-expert-mesh-fixture-replay.json
  examples/knowledge-intelligence/domain-expert-mesh-incident.json
  examples/knowledge-intelligence/domain-expert-mesh-operator-review.json
  examples/knowledge-intelligence/domain-expert-mesh-runtime-hold.json
)
for path in "${json_files[@]}"; do
  "$PYTHON_BIN" -m json.tool "$path" >/dev/null
done

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

from aion_brain.contracts.knowledge_domain_expert_mesh import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    DomainExpertMeshResourceBudget,
)
from aion_brain.knowledge_intelligence.domain_expert_profiles import (
    TOP_LEVEL_DOMAIN_IDS,
    build_default_domain_taxonomy,
    build_default_profile_registry,
)

ROOT = Path(os.environ["AION_REPO_ROOT"])
required_sources = (
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py",
)
for relative in required_sources:
    if not (ROOT / relative).is_file():
        raise SystemExit(f"required AION-213 source missing: {relative}")

budget = DomainExpertMeshResourceBudget()
if budget.maximum_persistent_mesh_write_batch != 0:
    raise SystemExit("persistent mesh write batch must remain zero")
if any(
    value != 0
    for value in (
        budget.maximum_model_provider_calls,
        budget.maximum_tool_executions,
        budget.maximum_network_calls,
        budget.maximum_connector_calls,
        budget.maximum_knowledge_promotions,
        budget.maximum_belief_mutations,
    )
):
    raise SystemExit("prohibited runtime budgets must remain zero")

taxonomy = build_default_domain_taxonomy()
registry = build_default_profile_registry(taxonomy)
if set(TOP_LEVEL_DOMAIN_IDS) - set(taxonomy.top_level_domain_ids):
    raise SystemExit("default taxonomy missing required top-level domains")
if any(profile.human_identity_claimed for profile in registry.profiles):
    raise SystemExit("profile human identity claim detected")
if any(profile.professional_credential_claimed for profile in registry.profiles):
    raise SystemExit("profile professional credential claim detected")
if any(profile.model_provider_required for profile in registry.profiles):
    raise SystemExit("profile model provider requirement detected")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [
    item
    for item in auth["records"]
    if item.get("authorization_transaction_id") == AUTHORIZATION_TRANSACTION_ID
]
if len(active) != 1:
    raise SystemExit("active AION-212-KI-0005 authorization record missing")
record = active[0]
post_aion214 = program.get("program_state") in {
    "tool_verification_fabric_authorized_not_implemented",
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout",
    "verified_knowledge_memory_authorized_not_implemented",
}
if post_aion214:
    if record["authorization_active"] is not False:
        raise SystemExit("AION-212-KI-0005 must be inactive after AION-214")
    if record["authorization_consumed"] is not True:
        raise SystemExit("AION-212-KI-0005 must be consumed after AION-214")
    if record["authorization_expired"] is not True or record["authorization_reusable"] is not False:
        raise SystemExit("AION-212-KI-0005 closeout lifecycle mismatch")
    if record.get("authorization_closed_by_task") != "AION-214":
        raise SystemExit("AION-212-KI-0005 must be closed by AION-214")
    successor = [item for item in auth["records"] if item.get("authorization_active") is True]
    expected_successor = (
        "AION-216-KI-0007"
        if program.get("program_state") == "verified_knowledge_memory_authorized_not_implemented"
        else "AION-214-KI-0006"
    )
    if len(successor) != 1 or successor[0].get("authorization_transaction_id") != expected_successor:
        raise SystemExit(f"{expected_successor} must be the sole active authorization")
else:
    if record["authorization_active"] is not True:
        raise SystemExit("AION-212-KI-0005 must remain active")
    if record["authorization_consumed"] is not False:
        raise SystemExit("AION-212-KI-0005 must remain unconsumed pending AION-214")
    if record["authorization_expired"] is not False or record["authorization_reusable"] is not False:
        raise SystemExit("AION-212-KI-0005 lifecycle mismatch")
if record["implementation_task"] != IMPLEMENTATION_TASK:
    raise SystemExit("authorization implementation task mismatch")
if record["formal_closeout_task"] != FORMAL_CLOSEOUT_TASK:
    raise SystemExit("authorization closeout task mismatch")
if record["authorization_scope"] != AUTHORIZATION_SCOPE:
    raise SystemExit("authorization scope mismatch")

for relative in (
    "docs/knowledge-intelligence/authorization-ledger.json",
    "docs/knowledge-intelligence/program-ledger.json",
):
    ledger = json.loads((ROOT / relative).read_text())
    if post_aion214:
        expected_projection = (
            ("AION-216-KI-0007", "AION-217", "AION-218")
            if ledger.get("program_state") == "verified_knowledge_memory_authorized_not_implemented"
            else ("AION-214-KI-0006", "AION-215", "AION-216")
        )
        if ledger["authorization_transaction_id"] != expected_projection[0]:
            raise SystemExit(f"successor projection mismatch for {relative}: authorization")
        if ledger["implementation_task"] != expected_projection[1]:
            raise SystemExit(f"successor projection mismatch for {relative}: implementation task")
        if ledger["formal_closeout_task"] != expected_projection[2]:
            raise SystemExit(f"successor projection mismatch for {relative}: closeout")
    else:
        for key in (
            "authorization_transaction_id",
            "candidate_id",
            "workstream",
            "implementation_task",
            "formal_closeout_task",
        ):
            if ledger[key] != record[key]:
                raise SystemExit(f"current-state projection mismatch for {relative}: {key}")
    if ledger["domain_expert_mesh_implemented"] is not True:
        raise SystemExit(f"mesh implementation flag missing in {relative}")
    for key in (
        "domain_expert_mesh_runtime_enabled",
        "persistent_expert_mesh_write_enabled",
        "expert_mesh_database_enabled",
        "model_provider_integration_enabled",
        "model_call_enabled",
        "tool_execution_enabled",
        "network_access_enabled",
        "human_expert_identity_claim_enabled",
        "professional_credential_claim_enabled",
        "absolute_truth_oracle_enabled",
        "automatic_claim_acceptance_enabled",
        "automatic_claim_rejection_enabled",
        "consensus_as_truth_enabled",
        "panel_size_confidence_amplification_enabled",
        "dissent_suppression_enabled",
        "autonomous_real_world_action_enabled",
        "high_stakes_action_enabled",
        "knowledge_promotion_enabled",
        "cognitive_belief_mutation_enabled",
        "runtime_effect",
    ):
        if ledger.get(key) is not False:
            raise SystemExit(f"prohibited flag enabled in {relative}: {key}")
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_domain_expert_mesh_*.py \
  services/brain-api/tests/test_knowledge_intelligence_current_projection.py \
  -q

./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

echo "knowledge intelligence domain expert mesh PASS"
