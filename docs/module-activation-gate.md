# Module Activation Request Gate

## Purpose

The Module Activation Request Gate gives AION Brain a records-first way to
evaluate future module activation without activating anything.

AION-083 creates metadata contracts, persistence, policy gates, API endpoints,
SDK methods, CLI commands, operator action visibility, audit posture, visual
telemetry vocabulary, and runtime registration previews.

## Non-Goals

This layer does not:

- Activate modules.
- Load extension code.
- Install packages.
- Register runtime routes.
- Register active capabilities.
- Mutate runtime configuration.
- Execute capabilities.
- Call external services.
- Enable full autonomy.
- Add domain-specific module logic.

## Flow

```text
module slot
-> capability binding
-> conformance/readiness evidence
-> activation request
-> activation gate run
-> blockers
-> review
-> non-executable activation plan
-> runtime registration preview
-> stop before activation
```

## Contracts

- `ModuleActivationRequest` records a future activation evaluation request.
- `ActivationBlocker` records missing requirements or disabled gates.
- `ActivationGateRun` records deterministic checks.
- `ActivationReview` records operator review.
- `ActivationPlan` records a non-executable plan.
- `RuntimeRegistrationPreview` records route/capability/policy/setting preview
  metadata without runtime registration.

All contracts remain AION-owned and must not expose SQLAlchemy rows,
third-party runtime objects, raw headers, raw prompts, hidden reasoning,
secrets, package bytes, or domain-specific internals.

## Gate Checks

The deterministic gate checks:

- Module slot metadata exists.
- Capability binding metadata exists.
- Readiness assessment evidence is present.
- Conformance evidence is present.
- Required policy actions are declared.
- Required settings are declared.
- Required sandbox profiles are declared.
- Module activation execution is disabled.
- Runtime registration is disabled.
- Unsafe activation metadata is absent.

The disabled activation and disabled runtime registration checks intentionally
produce critical blockers in AION-083.

## Runtime Registration Preview

Runtime registration preview records describe what might be registered in a
future task. They are not registration commands. They must keep:

- `would_register=false`
- `registration_allowed=false`
- `runtime_registration_enabled=false`

## Operator Visibility

Open `ActivationBlocker` records are surfaced through the Operator Action
Center as `module_activation_blocker` action items. This gives operators a
review queue without granting activation permissions.

## Policy Actions

The policy vocabulary includes `module_activation.*` and
`runtime.registration.preview.*` actions. Unsafe requests that imply source
mutation, code loading, activation, capability execution, runtime registration,
external calls, shell commands, or code generation fail closed.

## API

- `POST /brain/module-activation/requests`
- `GET /brain/module-activation/requests`
- `GET /brain/module-activation/requests/{activation_request_id}`
- `POST /brain/module-activation/requests/{activation_request_id}/archive`
- `DELETE /brain/module-activation/requests/{activation_request_id}`
- `POST /brain/module-activation/requests/{activation_request_id}/gate`
- `GET /brain/module-activation/requests/{activation_request_id}/gate-runs`
- `GET /brain/module-activation/blockers`
- `POST /brain/module-activation/blockers/{activation_blocker_id}/dismiss`
- `POST /brain/module-activation/reviews`
- `GET /brain/module-activation/reviews`
- `POST /brain/module-activation/requests/{activation_request_id}/plans`
- `GET /brain/module-activation/plans`
- `GET /brain/module-activation/plans/{activation_plan_id}`
- `POST /brain/module-activation/requests/{activation_request_id}/runtime-registration-preview`
- `GET /brain/module-activation/runtime-registration-previews`
- `GET /brain/module-activation/runtime-registration-previews/{registration_preview_id}`
- `POST /brain/module-activation/query`
