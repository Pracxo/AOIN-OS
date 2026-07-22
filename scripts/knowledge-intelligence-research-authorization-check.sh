#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}
for json_file in docs/knowledge-intelligence/program-ledger.json docs/knowledge-intelligence/authorization-ledger.json examples/knowledge-intelligence/*.json operator-console-static/demo-data/knowledge-intelligence*.json; do
  "$PYTHON_BIN" -m json.tool "$json_file" >/dev/null
done
"$PYTHON_BIN" - <<'__AION204_VALIDATE__'

import json
import os
import re
from pathlib import Path
ROOT = Path(os.environ.get('AION_REPO_ROOT', '.')).resolve()
PROGRAM_ID = 'AION-KNOWLEDGE-INTELLIGENCE-001'
AUTH_ID = 'AION-204-KI-0001'
PARENT_MAIN_COMMIT = 'fdc38402e050ffb5beebd9d6d298f859736f0121'
PARENT_DECISION = 'CONTROLLED_LOCAL_OFFLINE_PILOT_PASS_COMPLETE_COGNITIVE_ARCHITECTURE_PROGRAM'
APPROVED_KEYS = ['research_contracts_approved', 'research_plan_contract_approved', 'research_query_contract_approved', 'source_candidate_contract_approved', 'source_snapshot_contract_approved', 'source_provenance_contract_approved', 'citation_reference_contract_approved', 'source_lineage_contract_approved', 'research_evidence_bundle_approved', 'research_diagnostics_approved', 'research_incident_record_approved', 'domain_allowlist_policy_approved', 'url_canonicalization_approved', 'scheme_validation_approved', 'public_network_destination_validation_approved', 'private_network_rejection_approved', 'loopback_rejection_approved', 'link_local_rejection_approved', 'multicast_rejection_approved', 'reserved_address_rejection_approved', 'dns_rebinding_defence_approved', 'redirect_policy_approved', 'http_get_method_approved', 'http_head_method_approved', 'response_size_budget_approved', 'total_transfer_budget_approved', 'timeout_budget_approved', 'concurrency_budget_approved', 'content_type_policy_approved', 'character_encoding_validation_approved', 'safe_header_projection_approved', 'content_sha256_fingerprinting_approved', 'source_deduplication_approved', 'source_snapshot_immutability_approved', 'publication_timestamp_capture_approved', 'modification_timestamp_capture_approved', 'retrieval_timestamp_capture_approved', 'source_quality_classification_approved', 'robots_policy_metadata_approved', 'licence_policy_metadata_approved', 'operator_review_item_approved', 'disabled_research_adapter_approved', 'in_memory_research_adapter_approved', 'explicit_local_fixture_adapter_approved', 'explicit_operator_invoked_http_adapter_implementation_approved', 'research_adapter_protocol_approved', 'search_adapter_protocol_approved', 'fail_closed_research_policy_approved', 'synthetic_test_fixture_approved', 'documentation_and_static_evidence_approved', 'no_knowledge_promotion_enforcement_approved', 'no_cognitive_belief_mutation_enforcement_approved', 'no_background_crawl_enforcement_approved', 'no_runtime_registration_enforcement_approved', 'no_credential_use_enforcement_approved', 'no_source_mutation_enforcement_approved', 'no_git_mutation_enforcement_approved', 'no_pr_creation_enforcement_approved', 'no_approval_creation_enforcement_approved']
PROHIBITED_KEYS = ['research_runtime_enabled', 'automatic_research_enabled', 'background_crawler_enabled', 'scheduled_research_enabled', 'continuous_web_monitoring_enabled', 'kernel_registration_enabled', 'application_startup_registration_enabled', 'production_event_subscription_enabled', 'unrestricted_network_access_enabled', 'arbitrary_url_access_enabled', 'arbitrary_domain_access_enabled', 'private_network_access_enabled', 'localhost_access_enabled', 'link_local_access_enabled', 'unix_socket_access_enabled', 'file_scheme_access_enabled', 'ftp_access_enabled', 'websocket_access_enabled', 'javascript_execution_enabled', 'browser_automation_enabled', 'form_submission_enabled', 'http_post_enabled', 'http_put_enabled', 'http_patch_enabled', 'http_delete_enabled', 'file_upload_enabled', 'authentication_enabled', 'credential_use_enabled', 'cookie_use_enabled', 'authorization_header_use_enabled', 'login_flow_enabled', 'captcha_bypass_enabled', 'paywall_bypass_enabled', 'robots_bypass_enabled', 'access_control_bypass_enabled', 'private_content_access_enabled', 'personal_account_access_enabled', 'search_provider_integration_enabled', 'connector_integration_enabled', 'model_provider_integration_enabled', 'raw_prompt_storage_enabled', 'hidden_reasoning_storage_enabled', 'unredacted_personal_data_storage_enabled', 'full_source_content_repository_storage_enabled', 'automatic_cognitive_memory_ingestion_enabled', 'automatic_belief_creation_enabled', 'automatic_claim_verification_enabled', 'automatic_knowledge_promotion_enabled', 'user_statement_as_fact_enabled', 'engagement_signal_as_fact_enabled', 'source_patch_generation_enabled', 'source_mutation_enabled', 'worktree_creation_enabled', 'git_mutation_enabled', 'real_pull_request_creation_enabled', 'approval_creation_enabled', 'automatic_merge_enabled', 'production_canary_enabled', 'production_deployment_enabled', 'model_weight_training_enabled', 'runtime_effect', 'dependency_change_approved', 'migration_approved', 'github_workflow_change_approved', 'api_route_approved', 'installed_cli_command_approved', 'sdk_runtime_resource_approved', 'v02_tag_created', 'v02_release_created']
RESOURCE_LIMITS = {'maximum_queries_per_plan': 20, 'maximum_domains_per_plan': 20, 'maximum_source_candidates_per_plan': 100, 'maximum_fetches_per_plan': 50, 'maximum_redirects_per_fetch': 3, 'maximum_concurrency': 4, 'maximum_timeout_seconds_per_request': 20, 'maximum_wall_clock_seconds_per_plan': 900, 'maximum_response_bytes_per_source': 5242880, 'maximum_total_transfer_bytes_per_plan': 52428800, 'maximum_snapshot_records_per_plan': 100, 'maximum_safe_headers_per_snapshot': 32, 'maximum_citation_references_per_snapshot': 20, 'network_calls_during_AION_204': 0, 'research_runtime_enabled': False, 'background_crawls': 0, 'scheduled_research_runs': 0, 'knowledge_promotions': 0, 'cognitive_belief_mutations': 0, 'source_mutations': 0, 'git_operations': 0, 'real_pull_requests_created_by_runtime': 0, 'approvals_created_by_runtime': 0, 'production_exposure': 0, 'model_weight_changes': 0}
SOURCE_CLASSES = ['primary_authoritative', 'official_standard', 'official_government', 'peer_reviewed', 'vendor_primary', 'institutional_primary', 'reputable_secondary', 'community_unverified', 'unknown', 'disallowed']
THREATS = ['SSRF', 'DNS rebinding', 'redirect escape', 'private IP encoding bypass', 'IPv6 bypass', 'metadata-service access', 'malicious DNS', 'certificate failure', 'malicious compression', 'decompression bomb', 'oversized response', 'endless stream', 'slow response', 'content-type confusion', 'charset confusion', 'HTML active content', 'executable download', 'archive bomb', 'PDF parser risk', 'robots-policy ambiguity', 'licensing ambiguity', 'paywall bypass', 'authentication leakage', 'cookie leakage', 'referer leakage', 'private-content access', 'prompt injection in acquired content', 'source content instructing AION to ignore policy', 'citation spoofing', 'publication-date spoofing', 'source-author spoofing', 'mirrored-source duplication', 'copied misinformation appearing independently corroborated', 'SEO poisoning', 'domain impersonation', 'compromised authoritative source', 'stale information', 'changed pages', 'retractions and corrections', 'jurisdiction mismatch', 'version mismatch', 'source content promoted directly into memory', 'user engagement treated as fact', 'background crawler escape', 'uncontrolled research cost', 'evidence deletion', 'source snapshot tampering', 'research evidence mistaken for verified knowledge']
ROADMAP_TASKS = ['AION-204', 'AION-205', 'AION-206', 'AION-207', 'AION-208', 'AION-209', 'AION-210', 'AION-211', 'AION-212', 'AION-213', 'AION-214', 'AION-215', 'AION-216', 'AION-217', 'AION-218', 'AION-219', 'AION-220']
def j(p): return json.loads((ROOT / p).read_text())
def t(p): return (ROOT / p).read_text()
def main():
    for p in ['docs/knowledge-intelligence/program-ledger.json','docs/knowledge-intelligence/authorization-ledger.json','examples/knowledge-intelligence/research-authorization.json','examples/knowledge-intelligence/research-plan-boundary.json','examples/knowledge-intelligence/research-resource-budget.json','examples/knowledge-intelligence/research-source-policy.json','examples/knowledge-intelligence/research-runtime-hold.json','examples/knowledge-intelligence/research-operator-review-item.json','operator-console-static/demo-data/knowledge-intelligence-program.json','operator-console-static/demo-data/knowledge-intelligence-research-authorization.json','operator-console-static/demo-data/knowledge-intelligence-research-runtime-hold.json']:
        x = j(p); assert x['synthetic'] is True and x['read_only'] is True and x['redacted'] is True, p
    cp = j('docs/cognitive-architecture/program-ledger.json'); ca = j('docs/cognitive-architecture/authorization-ledger.json')
    assert cp['program_state'] == 'cognitive_architecture_program_complete'
    assert cp['controlled_local_offline_pilot_passed'] is True
    assert cp['active_cognitive_implementation_authorization_count'] == 0
    assert ca['active_cognitive_implementation_authorization_count'] == 0
    assert t('docs/cognitive-architecture/aion-203-postmerge-verification.md').find(PARENT_DECISION) != -1
    pg = j('docs/knowledge-intelligence/program-ledger.json'); au = j('docs/knowledge-intelligence/authorization-ledger.json')
    assert pg['program_id'] == PROGRAM_ID and pg['program_state'] == 'research_plane_authorized_not_implemented'
    assert pg['active_knowledge_implementation_authorization_count'] == 1 and pg['active_knowledge_implementation_authorization'] == AUTH_ID
    assert pg['active_knowledge_implementation_task'] == 'AION-205' and pg['formal_closeout_task'] == 'AION-206'
    for k in ['research_plane_implemented','research_runtime_enabled','network_access_enabled','knowledge_promotion_enabled','verified_knowledge_memory_enabled','automatic_belief_creation_enabled','background_crawler_enabled','production_exposure','model_weight_training_enabled']: assert pg[k] is False, k
    assert [x['task_id'] for x in pg['tasks']] == ROADMAP_TASKS
    assert au['active_cognitive_implementation_authorization_count'] == 0 and au['active_knowledge_implementation_authorization_count'] == 1
    active = [r for r in au['records'] if r.get('authorization_active') is True]
    assert len(active) == 1
    r = active[0]
    assert r['authorization_transaction_id'] == AUTH_ID and r['approval_record_id'] == AUTH_ID
    assert r['candidate_id'] == 'controlled-internet-research-acquisition-core' and r['implementation_task'] == 'AION-205' and r['formal_closeout_task'] == 'AION-206'
    assert r['authorization_scope'] == 'disabled-allowlisted-public-research-query-fetch-snapshot-provenance-core' and r['authorization_consumed'] is False and r['authorization_expired'] is False and r['authorization_reusable'] is False
    assert set(r['authorized_capabilities']) == set(APPROVED_KEYS) and all(r['authorized_capabilities'][k] is True for k in APPROVED_KEYS)
    assert set(r['prohibited_capabilities']) == set(PROHIBITED_KEYS) and all(r['prohibited_capabilities'][k] is False for k in PROHIBITED_KEYS)
    assert r['resource_limits'] == RESOURCE_LIMITS and r['source_quality_classes'] == SOURCE_CLASSES
    stale = re.compile(r'Current milestone:\s*AION-18[12]|AION-181 is the next task|AION-182.*next|actual_controlled_shadow_activation_authorization_review|current state remains AION-179|current stage remains AION-179')
    for p in ['README.md','AGENTS.md','docs/project-status.md','docs/architecture.md','docs/brain-contract.md','docs/policy-model.md','docs/visual-brain.md','docs/release/v02-release-readiness-delta.md','operator-console-static/README.md']:
        assert stale.search(t(p)) is None, p
    for doc in ['program-charter.md','architecture-roadmap.md','security-boundary.md','research-source-policy.md','research-threat-model.md','non-destructive-evolution.md']:
        assert (ROOT / 'docs/knowledge-intelligence' / doc).is_file(), doc
    for item in THREATS: assert item in t('docs/knowledge-intelligence/research-threat-model.md'), item
    for item in SOURCE_CLASSES: assert item in t('docs/knowledge-intelligence/research-source-policy.md'), item
    assert not (ROOT / 'services/brain-api/src/aion_brain/knowledge_intelligence').exists()
    assert not (ROOT / 'services/brain-api/src/aion_brain/contracts/knowledge_research.py').exists()
if __name__ == '__main__': main()

__AION204_VALIDATE__
if is_nested_gate_context; then
  echo "PASS: AION-203 GitHub verification deferred to outer gate"
else
  pr_json="$(gh pr view 114 --json number,state,mergedAt,mergeCommit,headRefName,headRefOid,baseRefName)"
  "$PYTHON_BIN" - <<'__AION204_PR__' "$pr_json"
import json, sys
p=json.loads(sys.argv[1])
assert p['number']==114 and p['state']=='MERGED' and p['baseRefName']=='main'
assert p['headRefName']=='phase/cognitive-local-offline-pilot-closeout'
assert p['headRefOid']=='24df1f990a643d013e6155f6ce32598dfa8833bd'
assert p['mergeCommit']['oid']=='fdc38402e050ffb5beebd9d6d298f859736f0121'
assert p['mergedAt']=='2026-07-22T18:55:59Z'
__AION204_PR__
  git merge-base --is-ancestor 24df1f990a643d013e6155f6ce32598dfa8833bd origin/main
  git merge-base --is-ancestor fdc38402e050ffb5beebd9d6d298f859736f0121 origin/main
  gh pr checks 114 | grep -E 'brain-api-quality[[:space:]]+pass' >/dev/null
  gh pr checks 114 | grep -E 'sdk-quality[[:space:]]+pass' >/dev/null
fi
./scripts/knowledge-intelligence-research-authorization-no-go-regression.sh
if is_nested_gate_context; then
  echo "PASS: inherited AION-204 gates deferred to outer gate"
else
  "$PYTHON_BIN" - <<'__AION204_AION203_INHERITED__'
import sys
from pathlib import Path

root = Path(".").resolve()
sys.path.insert(0, str(root / "scripts/lib"))
from cognitive_architecture_governance import (  # noqa: E402
    validate_local_offline_pilot_closeout,
    validate_no_go,
)

validate_local_offline_pilot_closeout(root)
validate_no_go(root)
print("PASS: inherited AION-203 closeout state and no-go safety validated")
__AION204_AION203_INHERITED__
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_cognitive_local_offline_pilot_closeout_docs.py \
    services/brain-api/tests/test_cognitive_local_offline_pilot_docs.py \
    services/brain-api/tests/test_cognitive_local_offline_pilot_authorization_docs.py \
    -q
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
  ./scripts/docs-check.sh
  ./scripts/final-docs-audit.sh
  ./scripts/verify-no-domain-drift.sh
  ./scripts/boundary-check.sh
fi
echo "knowledge intelligence research authorization PASS"
