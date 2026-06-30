# Connector Runtime Review Gate

## Purpose

AION-109 freezes the disabled connector runtime path before any future connector implementation. The gate proves the connector boundary, disabled prototype, preview-only surfaces, and no-go checks are aligned before the project moves toward simulator or implementation work.

## Scope Reviewed

The review covers connector boundary docs, trust and credential boundaries, egress and ingress guards, the disabled connector prototype, mock manifest validation, egress and ingress previews, connector runtime audit evidence, static console connector panels, policy checks, and repository boundary checks.

It does not add connector runtime implementation, network access, credential storage, token storage, external identity runtime, provider SDKs, connector SDKs, API routes, SDK resources, CLI commands, migrations, package files, module activation, capability activation, code loading, tool execution, or write paths.

## AION-106 And AION-108 Summary

AION-106 defined the external connector boundary. It established that connectors are untrusted by default, external calls remain disabled, credentials and tokens remain absent, and future connector work needs explicit review gates.

AION-108 added a disabled connector prototype. It added hard-off runtime status, mock manifest validation, egress preview, ingress preview, audit proof, static console demo evidence, and regression checks while keeping all external calls, activation, route registration, credentials, and token storage disabled.

## Current Safe State

The safe state is review-only and local-only. Connector artifacts are synthetic, preview-only, and redacted. The runtime status remains disabled, egress is blocked, ingress is untrusted, provenance is required, and no connector can register routes, activate capabilities, call external services, store secrets, or execute tools.

## What Remains Disabled

- `connector_runtime_enabled=false`
- `connector_external_calls_enabled=false`
- `connector_credentials_enabled=false`
- `connector_token_storage_enabled=false`
- `connector_activation_enabled=false`
- `connector_route_registration_enabled=false`
- network clients remain absent
- connector and provider SDK dependencies remain absent
- API router additions remain blocked for AION-109
- migrations and package files remain blocked

## What Remains Preview-Only

- mock connector manifest validation
- egress preview
- ingress preview
- connector runtime audit
- static console connector panel
- documentation and example evidence
- pre-implementation gate evidence

## Known Gaps

No production connector runtime exists. No credential store exists. No egress allowlist exists. No ingress trust elevation exists. No sandboxed connector execution exists. No route registration, activation path, or connector SDK integration exists. These gaps are intentional release blockers until future connector implementation phases satisfy the pre-implementation gate.

## Review Decision

The AION-109 review decision is to keep the connector runtime disabled and freeze the disabled connector safety baseline. Future connector work must pass this review gate and the no-external-call regression before implementation work can proceed.

## Next Phase Recommendation

Proceed to AION-110 only as disabled dry-run simulator hardening. No external calls are allowed until a later connector release gate passes with approved threat model, credential design, egress allowlist, ingress redaction, provenance, policy, operator review, and sandbox evidence.

## AION-110 Outcome

AION-110 adds the dry-run simulator, replay fixtures, policy readiness gate,
SDK/CLI access, static console evidence, and no-go regression checks. The
runtime review gate still blocks connector runtime enablement, external calls,
credential use, token use, route registration, activation, tool execution, and
write execution.

## AION-111 Outcome

AION-111 adds the connector policy action catalog, authorization matrix,
policy dry-run gate, denial rules, traceability records, SDK/CLI preview
access, static console policy preview data, and policy no-go regression. The
runtime review gate still blocks runtime allow paths, external calls,
credential use, token use, activation, route registration, tool execution, and
write execution.

## AION-112 Outcome

AION-112 adds the connector sandbox design boundary, isolation model,
capability rules, readiness preview, denials, audit/provenance records,
SDK/CLI preview access, static console sandbox preview data, and sandbox
no-go regression. The runtime review gate still blocks real sandbox execution,
filesystem access, network access, credential use, token use, process
spawning, dynamic imports, package installation, activation, route
registration, tool execution, and write execution.
## AION-114 Release Gate Input

The runtime review gate is a required input to
`./scripts/connector-release-gate.sh`. A failed runtime review blocks connector
release readiness and future implementation review.
