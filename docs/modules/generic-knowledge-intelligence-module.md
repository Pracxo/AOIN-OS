# Generic Knowledge Intelligence Module

## Purpose

The Generic Knowledge Intelligence Module is the first selected governed module
class for post-v0.1 strategy. It remains metadata-only in AION-082.

## What It Does

- Retrieves generic knowledge references already available through AION-owned
  records.
- Summarizes scoped material.
- Grounds candidate answers in citations and evidence references.
- Explains how an answer was assembled from allowed references.
- Answers generic questions through governed Brain contracts.

## What It Does Not Do

- It does not execute tools.
- It does not call external services.
- It does not install packages.
- It does not load code.
- It does not register routes.
- It does not activate capabilities.
- It does not request full autonomy.
- It does not modify Brain core.

## Required Brain Gates

- Extension manifest.
- Extension intake.
- Module slot.
- Capability binding.
- Binding validation.
- Conformance.
- Readiness assessment.
- Operator review.
- Policy, risk, audit, provenance, sandbox, RC, and freeze gates.

## Required Contracts

- Extension manifest.
- Capability binding.
- Conformance profile.
- Readiness assessment.
- Evidence references.
- Grounding records.
- Citation records.
- Prompt packet governance records.
- Model output governance records.
- Response candidate records.

## Required Policies

- `capability.list`
- `capability.register`
- `capability.invoke`
- `memory.retrieve`
- `context.compile`
- `trace.read`
- `model_output.parse`
- `prompt.compile`

## Required Conformance Profile

The conformance profile must verify declared schemas, capability metadata,
policy actions, sandbox requirement, risk level, no route declarations, no
external source declaration, no activation request, and no code payload.

## Synthetic Demo Flow

1. Submit metadata-only manifest.
2. Run extension intake.
3. Stage inactive module slot.
4. Create inactive capability bindings.
5. Validate bindings.
6. Run schema-only conformance.
7. Produce readiness assessment with `activation_ready=false`.
8. Record operator review.

## Operator Review Path

The operator reviews declared capabilities, permissions, memory scope, risk
level, sandbox posture, conformance result, readiness assessment, and future
disable plan. Review does not activate the module.

## Activation Remains Disabled

Activation remains disabled. `activation_ready` remains false for AION-082.

## AION-084 Metadata Pack

AION-084 turns this selected module class into the first concrete metadata-only
module pack under `examples/modules/generic-knowledge-intelligence/`.

The pack contains:

- extension manifest
- intake dry-run request
- inactive module slot request
- five inactive capability binding requests
- binding validation request
- conformance profile
- synthetic test vectors
- conformance run request
- readiness assessment request
- activation request
- activation gate expectation fixture
- operator review request

It remains a module package and readiness trail, not a runtime module.
Activation blockers are expected and successful in v0.1.

## Future Runtime Design

Future runtime design must add activation request semantics, approval
semantics, sandbox execution, runtime adapter boundaries, rollback, disable,
and release gates before this module can run.

AION-105 adds a module activation design review gate before that future runtime
design. The gate keeps Generic Knowledge Intelligence metadata-only and
requires plugin boundary evidence, disabled code-loading proof, disabled
runtime-registration proof, disabled capability-activation proof, lifecycle
traceability, and no-go regression evidence before any later implementation
task can proceed.

## Metadata-Only Capabilities

| Capability | Risk level | dry_run_supported | controlled_supported | requires_policy | requires_approval | requires_sandbox | External source | Code payload | Dynamic route |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `generic.knowledge.retrieve` | low | true | false | true | false | true | no | no | no |
| `generic.knowledge.summarize` | low | true | false | true | false | true | no | no | no |
| `generic.knowledge.ground` | medium | true | false | true | false | true | no | no | no |
| `generic.knowledge.explain` | low | true | false | true | false | true | no | no | no |
| `generic.knowledge.answer` | medium | true | false | true | false | true | no | no | no |
