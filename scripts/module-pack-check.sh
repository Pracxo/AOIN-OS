#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PACK_DIR="$ROOT_DIR/examples/modules/generic-knowledge-intelligence"

cd "$ROOT_DIR"

test -d "$PACK_DIR" || {
  echo "missing module pack directory: $PACK_DIR" >&2
  exit 1
}

python3 - <<'PY'
import json
from pathlib import Path

pack = Path("examples/modules/generic-knowledge-intelligence")
manifest_path = pack / "manifest.json"
for path in sorted(pack.glob("*.json")):
    with path.open() as handle:
        json.load(handle)

manifest = json.loads(manifest_path.read_text())
serialized_manifest = json.dumps(manifest, sort_keys=True).lower()

forbidden_terms = {
    "executable_payload",
    "source_url",
    "external_source",
    "install",
    "pip",
    "npm",
    "docker build",
    "full_autonomy\": true",
    "activation_enabled",
    "route_registration_enabled",
    "raw_secret_access\": true",
}
for term in forbidden_terms:
    if term in serialized_manifest:
        raise SystemExit(f"manifest contains forbidden term: {term}")

forbidden_keys = {
    "executable_payload",
    "code",
    "source_url",
    "external_source",
    "activation_enabled",
    "route_registration_enabled",
    "raw_secret_access",
}


def keys(value: object) -> set[str]:
    if isinstance(value, dict):
        found = {str(key).lower() for key in value}
        for nested in value.values():
            found.update(keys(nested))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for item in value:
            found.update(keys(item))
        return found
    return set()


present_keys = keys(manifest)
blocked = sorted(forbidden_keys & present_keys)
if blocked:
    raise SystemExit(f"manifest contains forbidden keys: {blocked}")

capabilities = manifest.get("declared_capabilities", [])
if not capabilities:
    raise SystemExit("manifest declares no capabilities")
for capability in capabilities:
    capability_key = capability.get("capability_key", "")
    if not capability_key.startswith("generic."):
        raise SystemExit(f"non-generic capability declared: {capability_key}")
    if capability.get("controlled_supported") is not False:
        raise SystemExit(f"controlled mode must be false for {capability_key}")

if manifest.get("declared_routes") != []:
    raise SystemExit("manifest must not declare routes")
if manifest.get("declared_dependencies") != []:
    raise SystemExit("manifest must not declare external dependencies")

bindings = json.loads((pack / "capability-bindings.json").read_text())
if len(bindings) != 5:
    raise SystemExit("capability binding fixture must declare five bindings")
for binding in bindings:
    if binding.get("target_runtime") != "metadata_only":
        raise SystemExit("capability binding target_runtime must be metadata_only")
    if binding.get("controlled_supported") is not False:
        raise SystemExit("capability binding controlled_supported must be false")
    if binding.get("dry_run_supported") is not True:
        raise SystemExit("capability binding dry_run_supported must be true")

activation = json.loads((pack / "activation-request.json").read_text())
activation_metadata = activation.get("metadata", {})
if activation_metadata.get("expected_activation_allowed") is not False:
    raise SystemExit("activation request must expect activation_allowed=false")
if activation_metadata.get("expected_execution_allowed") is not False:
    raise SystemExit("activation request must expect execution_allowed=false")
if activation_metadata.get("expected_registration_allowed") is not False:
    raise SystemExit("activation request must expect registration_allowed=false")

readiness = json.loads((pack / "readiness-assessment-request.json").read_text())
if readiness.get("metadata", {}).get("expected_activation_ready") is not False:
    raise SystemExit("readiness request must expect activation_ready=false")

gate = json.loads((pack / "activation-gate-request.json").read_text())
expected_blockers = set(gate.get("expect", {}).get("blockers", []))
for blocker in {
    "activation_disabled",
    "runtime_registration_disabled",
    "code_loading_disabled",
}:
    if blocker not in expected_blockers:
        raise SystemExit(f"activation gate expectation missing {blocker}")

for required in {
    "mock-profile.json",
    "mock-invocation-request.json",
    "mock-output-example.json",
    "mock-readiness-trail.json",
}:
    if not (pack / required).exists():
        raise SystemExit(f"missing module mock runtime fixture: {required}")

mock_profile = json.loads((pack / "mock-profile.json").read_text())
if mock_profile.get("profile_key") != "generic.knowledge.mock":
    raise SystemExit("mock profile must use generic.knowledge.mock")
if mock_profile.get("metadata", {}).get("activation_allowed") is not False:
    raise SystemExit("mock profile must keep activation_allowed=false")

mock_request = json.loads((pack / "mock-invocation-request.json").read_text())
if mock_request.get("mode") != "dry_run":
    raise SystemExit("mock invocation mode must be dry_run")
for key in {
    "activation_allowed",
    "execution_allowed",
    "external_calls_made",
    "code_loaded",
}:
    if mock_request.get("metadata", {}).get(key) is not False:
        raise SystemExit(f"mock invocation metadata must keep {key}=false")

mock_output = json.loads((pack / "mock-output-example.json").read_text())
if mock_output.get("redacted_output_payload", {}).get("synthetic") is not True:
    raise SystemExit("mock output example must be synthetic")
for key in {
    "activation_allowed",
    "execution_allowed",
    "external_calls_made",
    "code_loaded",
}:
    if mock_output.get("redacted_output_payload", {}).get(key) is not False:
        raise SystemExit(f"mock output must keep {key}=false")

mock_trail = json.loads((pack / "mock-readiness-trail.json").read_text())
if mock_trail.get("expected", {}).get("synthetic_output_only") is not True:
    raise SystemExit("mock readiness trail must expect synthetic_output_only=true")

print("Generic Knowledge Intelligence JSON fixtures valid")
PY

test -x "$PACK_DIR/demo-sequence.sh" || {
  echo "demo-sequence.sh must be executable" >&2
  exit 1
}
test -x "$ROOT_DIR/scripts/generic-knowledge-demo.sh" || {
  echo "generic-knowledge-demo.sh must be executable" >&2
  exit 1
}

echo "Module pack check PASS"
