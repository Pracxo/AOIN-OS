# Connector Release Gate

## Purpose

AION-114 consolidates the connector boundary, disabled runtime preview, runtime
review, dry-run simulator, policy catalog, sandbox design, and credential
architecture into one release gate. The gate proves future connector work is
blocked until explicit implementation approval exists.

This gate is evidence-only. It does not approve connector implementation, does
not enable connector runtime behavior, and does not add network, storage, auth,
sandbox, activation, or route-registration paths.

## Scope

The release gate covers connector artifacts produced by AION-106 through
AION-113:

- connector boundary design
- disabled connector runtime proof
- connector runtime review gate
- synthetic connector dry-run simulator
- connector policy action catalog and denial rules
- connector sandbox design and no-go checks
- connector credential store architecture boundary
- operator static console connector panels
- docs, examples, and regression scripts

## Required Prior Gates

The connector release gate requires these local gates to pass:

```bash
./scripts/connector-runtime-review.sh
./scripts/connector-runtime-no-external-call-regression.sh
./scripts/connector-simulator-check.sh
./scripts/connector-simulator-no-go-regression.sh
./scripts/connector-policy-check.sh
./scripts/connector-policy-no-go-regression.sh
./scripts/connector-sandbox-check.sh
./scripts/connector-sandbox-no-go-regression.sh
./scripts/connector-credential-check.sh
./scripts/connector-credential-no-go-regression.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
```

## Connector Runtime Disabled Checks

The gate fails if connector runtime enablement is found in settings, examples,
static console data, or connector release artifacts. The expected safe value is
`connector_runtime_enabled=false`.

## External Call Absence Checks

The gate fails if connector external calls, network clients, provider SDKs, or
runtime endpoint references are added. The expected safe value is
`external_calls_enabled=false`.

## Credential/Token Absence Checks

The gate fails if credential storage, token storage, raw material storage, OAuth,
OIDC, SAML, or external identity runtime paths are added. The expected safe
values are `credentials_present=false` and `token_storage_enabled=false`.

## Sandbox Execution Absence Checks

The gate fails if sandbox execution, filesystem access, network access, process
spawning, dynamic import, package installation, or connector activation is
enabled. The expected safe value is `sandbox_execution_enabled=false`.

## Policy Denial Checks

The gate requires connector policy denial rows to remain present for runtime
allow paths, external calls, storage material, sandbox execution, activation,
route registration, and provider integration. The policy catalog remains
preview-only and dry-run-only.

## Dry-Run Simulator Checks

The synthetic connector simulator can generate preview evidence only. The gate
fails if simulator evidence becomes execution, network access, provider access,
storage access, or route registration.

## Static Console Checks

The static console may show release gate status and safety freeze evidence from
bundled JSON only. It must not add inputs, write actions, credential entry,
runtime buttons, browser storage, external calls, or package dependencies.

## Documentation Checks

Release evidence requires current connector docs, ADR 0105 in the ADR index,
valid JSON examples, no domain drift, and the boundary checker passing.

## Release Blocker Conditions

Any of the following blocks connector release readiness:

- connector runtime enabled
- external calls enabled
- credentials or tokens stored
- OAuth, OIDC, or SAML runtime enabled
- sandbox execution enabled
- filesystem, network, process, import, or install access enabled
- policy runtime allow path added
- connector activation enabled
- connector route registration enabled
- provider SDK dependency added
- migration added
- package manager file added
- API runtime execution route added
- implementation approval set to true

## Pass/Fail Criteria

The gate passes only when all prior gates pass, release examples remain
synthetic, all safe-state booleans are false, implementation approval is false,
ADR 0105 is indexed, static demo data is present, and repository boundary checks
remain green.

## AION-115 Checkpoint Input

The connector release gate is a prerequisite for the connector platform
checkpoint. AION-115 uses this gate as evidence and keeps implementation
approval false.
