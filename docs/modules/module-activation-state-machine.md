# Module Activation State Machine

## State Definitions

- `manifest_submitted`: a module manifest has been received as metadata.
- `intake_validated`: extension intake accepted the manifest shape.
- `package_registered`: a package record exists.
- `slot_staged`: an inactive module slot exists.
- `binding_created`: inactive capability bindings exist.
- `binding_validated`: binding validation passed.
- `conformance_passed`: schema-only conformance passed.
- `readiness_reviewed`: readiness assessment exists.
- `operator_approved`: operator review is recorded.
- `activation_requested`: a future activation request exists.
- `activation_blocked_by_default`: v0.1 and AION-082 terminal stop.
- `future_activation_ready`: future design gate has cleared.
- `future_activated`: future runtime activation has occurred.
- `disabled`: module is disabled.
- `archived`: module records are retained for historical review.

## Allowed Transitions

```text
manifest_submitted -> intake_validated
intake_validated -> package_registered
package_registered -> slot_staged
slot_staged -> binding_created
binding_created -> binding_validated
binding_validated -> conformance_passed
conformance_passed -> readiness_reviewed
readiness_reviewed -> operator_approved
operator_approved -> activation_requested
activation_requested -> activation_blocked_by_default
future_activation_ready -> future_activated
future_activated -> disabled
disabled -> archived
```

## Blocked Transitions

- Any transition that skips policy.
- Any transition that skips audit/provenance.
- Any transition that skips conformance.
- Any transition that skips readiness assessment.
- Any transition that skips operator review.
- Any transition that activates code in AION-082.

## Required Evidence Per Transition

- Intake: manifest validation result.
- Package: package metadata and provenance reference.
- Slot: inactive slot record.
- Binding: inactive binding record.
- Validation: binding validation report.
- Conformance: conformance run and findings.
- Readiness: readiness assessment with `activation_ready=false`.
- Operator approval: review record and constraints.
- Activation request: future request record and policy decisions.

## No-Go Transitions

- `manifest_submitted -> future_activated`
- `binding_created -> future_activated`
- `conformance_passed -> future_activated`
- `readiness_reviewed -> future_activated`
- `operator_approved -> future_activated` without activation gate

## Future Activation Unlock Criteria

Future activation requires activation request design, approval semantics,
sandbox execution, runtime adapter boundaries, rollback, disable, policy
coverage, audit/provenance coverage, RC gate, freeze gate, and operator review.

In AION-083, `activation_requested` can be represented by a persisted
`ModuleActivationRequest`, but the only allowed next runtime state remains
`activation_blocked_by_default`. Activation, execution, code loading, package
installation, and runtime registration remain disabled.

## Generic Knowledge Intelligence Mapping

The AION-084 module pack maps to the state machine as evidence only:

- `manifest_submitted`: `manifest.json`
- `intake_validated`: `intake-request.json`
- `slot_staged`: `module-slot-request.json`
- `binding_created`: `capability-bindings.json`
- `binding_validated`: `binding-validation-request.json`
- `mock_runtime_evidence_recorded`: `mock-readiness-trail.json`
- `conformance_passed`: `conformance-run-request.json`
- `readiness_reviewed`: `readiness-assessment-request.json`
- `activation_requested`: `activation-request.json`
- `activation_blocked_by_default`: `activation-gate-request.json`
- `operator_approved`: `operator-review-request.json`

The expected terminal state for v0.1 is still
`activation_blocked_by_default`.

## Static Dashboard Representation

AION-090 represents the v0.1 path in a static local dashboard. The dashboard
shows `activation_blocked_by_default` through visible blockers and safety
labels. It does not create a transition to future activation and does not
change the state machine.

## AION-105 Review Gate

AION-105 reviews this state machine without adding a new runtime transition.
The expected terminal state remains `activation_blocked_by_default`.

Future movement from `activation_blocked_by_default` to
`future_activation_ready` requires the module activation pre-gate, a threat
model, sandbox design, package trust model, rollback design, operator approval
model, audit/provenance design, production auth dependency review, and release
gate. The AION-105 no-go regression fails if code loading, package
installation, dynamic route registration, runtime registration, capability
activation, controlled execution, module writes, policy bypass, or audit bypass
appears before that future review.
