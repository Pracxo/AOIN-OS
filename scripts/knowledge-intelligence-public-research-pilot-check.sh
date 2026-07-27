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
export AION_PUBLIC_RESEARCH_PILOT_CHECK_RUNNING=1

run_inherited_gate() {
  AION_AGGREGATE_GATE_RUNNING=1 "$@"
}

./scripts/knowledge-intelligence-public-research-pilot-no-go-regression.sh
./scripts/knowledge-intelligence-public-research-pilot-authorization-check.sh

PYTHONPATH="$ROOT_DIR/scripts/lib:$ROOT_DIR/services/brain-api/src:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import ipaddress
from pathlib import Path

import knowledge_intelligence_public_research_pilot_authorization as auth
from aion_brain.contracts.knowledge_public_research_pilot import (
    AUTHORIZATION_TRANSACTION_ID,
    PUBLIC_RESEARCH_RESOURCE_LIMITS,
    PublicResearchPilotMode,
    PublicResearchPilotPlan,
    PublicResearchPilotSourceCandidate,
)
from aion_brain.knowledge_intelligence.public_research_dns import (
    DisabledPublicResearchDnsBackend,
    PublicResearchDnsError,
    classify_public_address,
)
from aion_brain.knowledge_intelligence.public_research_http_transport import (
    DisabledPublicResearchConnectionBackend,
)
from aion_brain.knowledge_intelligence.public_research_integrity import (
    audit_public_research_pilot_integrity,
    passing_public_research_integrity_checks,
)
from aion_brain.knowledge_intelligence.public_research_policy import (
    PublicResearchPolicyError,
    canonicalize_public_research_url,
    evaluate_redirect_location,
    evaluate_x_robots_header,
    fixed_request_headers,
    parse_content_type_header,
    response_policy_decision,
    robots_url_for_source,
    validate_method,
    validate_response_body_size,
)

root = Path(os.environ["AION_REPO_ROOT"])

source_paths = (
    "services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py",
)
for relative in source_paths:
    if not (root / relative).is_file():
        raise SystemExit(f"missing exact AION-219 source path: {relative}")

auth.validate_authorization_files(root)
auth.validate_runtime_hold(root)

for relative in (
    "examples/knowledge-intelligence/public-research-pilot-authorization-envelope-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-plan-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-source-candidate-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-claim-specification-v1.json",
    "examples/knowledge-intelligence/public-research-dns-resolution-v1.json",
    "examples/knowledge-intelligence/public-research-http-exchange-v1.json",
    "examples/knowledge-intelligence/public-research-redirect-hop-v1.json",
    "examples/knowledge-intelligence/public-research-pipeline-trace-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-session-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-result-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-budget-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-integrity-report-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-evidence-bundle-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-operator-review-v1.json",
    "examples/knowledge-intelligence/public-research-pilot-authorization.json",
    "examples/knowledge-intelligence/public-research-pilot-runtime-hold.json",
):
    json.loads((root / relative).read_text(encoding="utf-8"))

plan = PublicResearchPilotPlan.model_validate(
    json.loads(
        (root / "examples/knowledge-intelligence/public-research-pilot-plan.json").read_text(
            encoding="utf-8"
        )
    )
)
if plan.mode is not PublicResearchPilotMode.DETERMINISTIC_SIMULATION:
    raise SystemExit("example plan must remain deterministic")
if not all(candidate.scheme == "https" for candidate in plan.explicit_source_candidates):
    raise SystemExit("source candidates must be HTTPS only")
budget_values = plan.resource_budget.model_dump(mode="json")
budget_values.pop("schema_version", None)
if budget_values != PUBLIC_RESEARCH_RESOURCE_LIMITS:
    raise SystemExit("resource limits drifted")

source = PublicResearchPilotSourceCandidate.model_validate(
    json.loads(
        (
            root
            / "examples/knowledge-intelligence/public-research-pilot-source-candidate.json"
        ).read_text(encoding="utf-8")
    )
)
canonical = canonicalize_public_research_url(source.original_url)
if not canonical.startswith("https://"):
    raise SystemExit("canonical source URL must be HTTPS")
if robots_url_for_source(canonical) != f"https://{source.domain}/robots.txt":
    raise SystemExit("robots URL derivation drifted")
if validate_method("GET") != "GET" or validate_method("HEAD") != "HEAD":
    raise SystemExit("GET/HEAD policy drifted")
if fixed_request_headers(("text/html", "text/plain"))["Accept-Encoding"] != "identity":
    raise SystemExit("identity content encoding policy drifted")
try:
    response_policy_decision(
        method="GET",
        status_code=200,
        headers={"Content-Encoding": "gzip"},
        maximum_response_bytes=100,
        allowed_content_types=("text/plain",),
    )
except PublicResearchPolicyError as exc:
    if exc.outcome.value != "rejected_content_encoding":
        raise SystemExit("compressed response rejection drifted") from exc
else:
    raise SystemExit("compressed response rejection drifted")
content_type, charset = parse_content_type_header("text/plain; charset=utf-8")
if (content_type, charset) != ("text/plain", "utf-8"):
    raise SystemExit("content-type policy drifted")
if evaluate_x_robots_header(("noindex",))[0] is True:
    raise SystemExit("X-Robots noindex must block")
validate_response_body_size(
    1,
    maximum_response_bytes=1,
    total_transfer_bytes=0,
    maximum_total_transfer_bytes=1,
)
if evaluate_redirect_location(
    current_url="https://example.com/a",
    location="https://example.com/b",
    allowlist=("example.com",),
    seen_urls=(),
) != "https://example.com/b":
    raise SystemExit("redirect policy drifted")

if classify_public_address(ipaddress.ip_address("8.8.8.8")).value != "resolved_and_pinned":
    raise SystemExit("public-address validation drifted")
for private in ("127.0.0.1", "10.0.0.1", "169.254.169.254"):
    if classify_public_address(ipaddress.ip_address(private)).value == "resolved_and_pinned":
        raise SystemExit(f"private destination accepted: {private}")

disabled_dns = DisabledPublicResearchDnsBackend()
disabled_http = DisabledPublicResearchConnectionBackend()
if disabled_dns.system_dns_resolution_available is not False:
    raise SystemExit("default DNS backend must be disabled")
if disabled_http.system_http_transport_available is not False:
    raise SystemExit("default HTTPS backend must be disabled")
try:
    disabled_dns.resolve("example.com", 443, resolution_id="resolution-0001")
except PublicResearchDnsError:
    pass
else:
    raise SystemExit("disabled DNS backend did not fail closed")

integrity = audit_public_research_pilot_integrity(
    report_id="integrity-0001",
    checks=passing_public_research_integrity_checks(),
)
if not integrity.passed:
    raise SystemExit("integrity audit baseline failed")

adr_readme = (root / "docs/adr/README.md").read_text(encoding="utf-8")
if "0183-controlled-operator-invoked-public-https-research-and-verified-candidate-pilot.md" not in adr_readme:
    raise SystemExit("ADR 0183 is not indexed")

for relative, marker in (
    ("docs/project-status.md", "AION-219 controlled public HTTPS research and verified-candidate pilot implemented"),
    ("docs/knowledge-intelligence/architecture-roadmap.md", "AION-219"),
    ("docs/knowledge-intelligence/program-ledger.json", "AION-220"),
    ("docs/knowledge-intelligence/authorization-ledger.json", AUTHORIZATION_TRANSACTION_ID),
):
    if marker not in (root / relative).read_text(encoding="utf-8"):
        raise SystemExit(f"missing marker {marker!r} in {relative}")
PY

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_knowledge_public_research_*.py \
  services/brain-api/tests/test_knowledge_intelligence_aion218_delivery_reconciliation.py \
  services/brain-api/tests/test_knowledge_intelligence_current_state_consistency.py \
  -q

run_inherited_gate ./scripts/knowledge-intelligence-verified-memory-operator-evaluation-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-verified-knowledge-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-check.sh
run_inherited_gate ./scripts/knowledge-intelligence-tool-verification-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-domain-expert-mesh-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-epistemic-truth-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-claim-graph-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-source-registry-runtime-hold.sh
run_inherited_gate ./scripts/knowledge-intelligence-research-runtime-hold.sh

if [[ -f examples/knowledge-intelligence/public-research-pilot-live-evidence-redacted.json ]]; then
  ./scripts/knowledge-intelligence-public-research-pilot-live-evidence-check.sh
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence public research pilot PASS"
