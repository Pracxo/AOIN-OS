# Generic Knowledge Intelligence Readiness Trail

## Purpose

The readiness trail is the evidence path for the metadata-only Generic
Knowledge Intelligence module pack. It lets an operator inspect every gate
without activating the module.

## Evidence Trail

```text
manifest
  -> extension intake
  -> module slot
  -> capability bindings
  -> binding validation
  -> conformance run
  -> readiness assessment
  -> activation request
  -> activation gate
  -> activation blockers
  -> runtime registration preview
  -> operator review
```

## Required Records

- Extension manifest metadata.
- Extension intake dry-run record.
- Inactive module slot metadata.
- Five inactive capability binding records.
- Binding validation dry-run record.
- Conformance profile and synthetic test vectors.
- Conformance run record.
- Readiness assessment with `activation_ready=false`.
- Future activation request with activation and execution denied.
- Activation gate run with safe blockers.
- Runtime registration preview with `registration_allowed=false`.
- Operator review record stating approval does not activate.

## Expected References

The demo fixtures use stable local references:

- `gki-intake-dry-run-001`
- `gki-module-slot-001`
- `gki-binding-retrieve-001`
- `gki-binding-summarize-001`
- `gki-binding-ground-001`
- `gki-binding-explain-001`
- `gki-binding-answer-001`
- `gki-conformance-profile-001`
- `gki-conformance-run-001`
- `gki-readiness-assessment-001`
- `gki-activation-request-001`

## Conformance Expectations

The conformance profile requires:

- `manifest_valid`
- `required_policy_actions_present`
- `sandbox_declared`
- `input_schema_valid`
- `output_schema_valid`
- `mock_invocation_valid`
- `no_activation_enabled`
- `no_code_loading`
- `no_external_source`
- `no_secret_schema`
- `no_domain_logic`

Synthetic test vectors use schema-only and mock-input payloads. They contain no
real user data, no secrets, no raw prompt text, and no hidden reasoning.

## Readiness Expectations

Readiness remains not ready for activation in v0.1:

- `require_approved_review=true`
- `require_passing_conformance=true`
- `activation_ready=false`
- operator review may be pending or recorded as future-only
- module mock runtime evidence may exist, but it is synthetic dry-run evidence
  only

## Activation Remains Blocked

The activation gate must produce safe blockers. Expected blocker categories are:

- activation disabled
- runtime registration disabled
- dynamic route registration disabled
- code loading disabled

These blockers are successful evidence in v0.1. They prove the module cannot
become active through the demo trail.

## Operator Handoff

The operator receives:

- fixture list
- demo command output
- mock runtime dry-run summary
- conformance expectations
- readiness expectations
- blocker summary
- no-go list
- ADR 0075 decision

## Release And Freeze Implications

AION-085 adds deterministic mock runtime evidence after the metadata-only
module pack. It does not move the `aion-v0.1.0` tag, add external
dependencies, enable runtime activation, load code, install packages, execute
capabilities, call external services, or add domain-specific logic.
