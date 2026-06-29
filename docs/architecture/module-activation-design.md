# Module Activation Design

## Purpose

This document defines the future activation design for AION modules. It is a
design artifact only. It does not implement runtime activation.

## Current v0.1 State

AION Brain v0.1.0 can intake metadata, stage module slots, create inactive
capability bindings, run conformance, and produce readiness assessments.
Activation remains disabled, code loading remains disabled, and package
installation remains disabled.

## Existing Gates Available

- Extension manifest.
- Extension intake.
- Module slot.
- Capability binding.
- Binding validation.
- Conformance.
- Readiness assessment.
- Operator review.
- Action proposal where needed.
- Policy, risk, approval, autonomy, sandbox, audit, provenance, RC, and freeze.

## Future Activation State Machine

```text
manifest_submitted
-> intake_validated
-> package_registered
-> slot_staged
-> binding_created
-> binding_validated
-> conformance_passed
-> readiness_reviewed
-> operator_approved
-> activation_requested
-> activation_blocked_by_default
-> future_activation_ready
-> future_activated
-> disabled
-> archived
```

In v0.1, AION-082, and AION-083, all activation paths stop at
`activation_blocked_by_default`.

## Required Records Before Activation

- Accepted extension manifest.
- Package record.
- Module slot record.
- Capability binding record.
- Binding validation result.
- Conformance run.
- Readiness assessment.
- Operator review.
- Policy decision records.
- Risk and sandbox posture records.
- Audit and provenance links.
- Rollback and disable plan.

## Required Checks Before Activation

- Manifest schema validity.
- No executable payload.
- No external dependency download.
- No dynamic route registration.
- No full autonomy request.
- No raw secret access request.
- Declared contracts exist.
- Declared settings exist.
- Sandbox requirement declared.
- Capability binding validates.
- Conformance passes.
- Readiness reviewed.
- Release and freeze gates remain green.

## Activation Request Semantics

A future activation request is a request to move a reviewed module from staged
metadata into a controlled runtime boundary. It is not a package install, code
load, route registration, or execution command by itself.

AION-083 implements the first activation request records, deterministic gate
runs, blockers, reviews, non-executable plans, and runtime registration
previews. The implementation still stops before activation and keeps
`activation_allowed=false`, `execution_allowed=false`, and
`registration_allowed=false`.

## Activation Approval Semantics

Approval must be explicit, scoped, revocable, and audit-backed. Approval cannot
grant permissions the policy layer would deny, and approval cannot bypass
sandbox requirements.

## Runtime Registration Boundaries

Runtime registration must remain behind a Brain-owned adapter. Public AION
contracts must not expose runtime-specific objects, package internals, or
framework-specific handles.

No runtime route registration exists in AION-082 or AION-083.

## Sandbox Requirements

Future activation requires a sandbox profile before any module runtime can be
considered. A sandbox profile must define network posture, file access,
resource limits, secret boundaries, and observable execution records.

## Policy Requirements

Future activation must pass policy before activation request, activation
approval, runtime registration, capability invocation, memory access, external
source use, and disable or rollback actions.

## Audit and Provenance Requirements

Every transition must record actor, scope, trace, inputs, decision, outcome,
and provenance references. Records must remain redacted and must not include
secrets, unredacted model input, provider payloads, or raw headers.

## Rollback and Disable Plan

Every future activation must include a disable plan before it can be approved.
Disable must stop future routing, revoke bindings, preserve audit records, and
avoid hard delete.

## Why Activation Remains Disabled in v0.1

Activation remains disabled because AION needs dedicated design gates for
runtime registration, sandbox execution, package provenance, operator approval,
policy coverage, rollback, and release discipline before code can run.

## Future Implementation Sequence

1. Activation request contract, still disabled.
2. Activation approval records, still disabled.
3. Non-executing mock runtime.
4. Sandbox execution design.
5. Runtime adapter implementation behind AION contracts.
6. Operator activation review.
7. Release candidate and freeze gates for activation.

## AION-105 Design Review Gate

AION-105 freezes this design before implementation. The design review lives in
`docs/modules/module-activation-design-review.md` and is backed by:

- `docs/modules/plugin-boundary-evidence-pack.md`
- `docs/modules/module-activation-pre-gate.md`
- `docs/modules/code-loading-disabled-proof.md`
- `docs/modules/runtime-registration-disabled-proof.md`
- `docs/modules/capability-activation-disabled-proof.md`
- `docs/modules/module-lifecycle-traceability-matrix.md`
- `docs/modules/future-activation-implementation-prerequisites.md`
- `docs/modules/module-activation-no-go-regression-pack.md`

After AION-105, activation remains disabled. No plugin loader, package
installer, dynamic import path, runtime registration path, active capability
path, controlled execution path, or module write path is approved.

Future activation work must pass `./scripts/module-activation-design-review.sh`
and `./scripts/module-activation-no-go-regression.sh` before implementation.
