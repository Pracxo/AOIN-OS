# Module Lifecycle Traceability Matrix

## Purpose

This matrix maps the current module lifecycle from manifest to evidence script.
It proves the lifecycle remains review-only after AION-105.

| Stage | Artifact | Evidence refs | Blockers | Activation state | Evidence script |
| --- | --- | --- | --- | --- | --- |
| manifest | extension manifest | `manifest.json` | executable payload, external source, dependency fetch | disabled | `./scripts/module-pack-check.sh` |
| intake | extension intake | `intake-request.json` | invalid manifest, unsafe package posture | disabled | `./scripts/module-pack-check.sh` |
| slot | module slot | `module-slot-request.json` | inactive slot required | disabled | `./scripts/module-pack-check.sh` |
| binding | capability bindings | `capability-bindings.json` | controlled support must be false | disabled | `./scripts/module-pack-check.sh` |
| validation | binding validation | `binding-validation-request.json` | binding mismatch, runtime target mismatch | disabled | `./scripts/module-pack-check.sh` |
| conformance | conformance run | `conformance-run-request.json` | schema failure, unsafe manifest shape | disabled | `./scripts/module-pack-check.sh` |
| readiness | readiness assessment | `readiness-assessment-request.json` | `activation_ready=false` required | disabled | `./scripts/module-pack-check.sh` |
| activation request | activation request | `activation-request.json` | activation, execution, and registration denied | disabled | `./scripts/module-pack-check.sh` |
| activation gate | activation gate request | `activation-gate-request.json` | activation disabled, runtime registration disabled, code loading disabled | disabled | `./scripts/module-activation-no-go-regression.sh` |
| blockers | blocker ledger | Operator Console blocker JSON | blocker visibility required | disabled | `./scripts/module-lifecycle-dashboard-check.sh` |
| registration preview | runtime registration preview | preview records | `registration_allowed=false` required | disabled | `./scripts/module-activation-no-go-regression.sh` |
| mock runtime | synthetic mock runtime | mock profile, invocation, output, trail | synthetic only, no code loaded | mock-only | `./scripts/module-lifecycle-dashboard-check.sh` |
| operator review | operator review | review checklist | review cannot activate | disabled | `./scripts/module-lifecycle-dashboard-check.sh` |
| audit/provenance | review evidence | release and freeze evidence | audit bypass blocked | disabled | `./scripts/operator-platform-freeze-gate.sh` |
| evidence script | composed review | AION-105 scripts | failed row blocks release | disabled | `./scripts/module-activation-design-review.sh` |

## Traceability Decision

Every lifecycle stage has local evidence and an explicit blocker. No row grants
activation, execution, registration, code loading, package installation, or
controlled handoff.
