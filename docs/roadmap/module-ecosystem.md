# Post-v0.1 Module Ecosystem

## Purpose

This document defines the post-v0.1 module ecosystem strategy for AION OS,
the Adaptive Intelligence Orchestration Nexus Operating System.

AION Brain v0.1.0 is the frozen local-first baseline. The next phase is not
runtime expansion. It is the strategy, activation design, review path, and
first metadata-only module selection needed before future modules can be
activated safely.

## v0.1 Baseline

AION Brain v0.1.0 remains local-first, dry-run safe by default, and
domain-neutral. It does not enable production auth, full autonomy, external
model calls by default, external notifications by default, extension code
loading, capability activation, dynamic route registration, hard delete,
model-generated tool execution, or domain modules in Brain core.

## Why Modules Start After Brain Freeze

The Brain core needed a stable release baseline before module work could
begin. That freeze gives future modules a fixed contract surface, a local
verification suite, release gates, and operator handoff rules.

Brain core is frozen after v0.1 except release-blocking fixes and
architecture-approved platform changes.

## Module Ecosystem Principles

- Modules must plug into Brain through metadata, contracts, bindings,
  conformance, readiness, and operator review.
- Domain modules must not modify Brain core.
- Modules never bypass policy, audit, provenance, prompt governance, model
  output governance, tool intent blocking, sandbox requirements, release
  gates, freeze gates, or operator review.
- Module examples remain metadata-only until activation design is complete.
- Activation design must be completed before runtime activation exists.

## Module Lifecycle

The post-v0.1 module path is:

```text
extension manifest
-> extension intake
-> module slot
-> capability binding
-> binding validation
-> conformance
-> readiness assessment
-> operator review
-> action proposal where needed
-> policy, risk, approval, autonomy, sandbox
-> future activation gate
```

## Module Intake Gates

Every module must pass:

- Manifest validation.
- Extension intake.
- Module slot staging.
- Capability binding validation.
- Conformance.
- Readiness assessment.
- Operator review.
- Policy, risk, approval, autonomy, sandbox, audit, and provenance checks.
- Release candidate and freeze gates before release.

## Activation Remains Disabled

Activation remains disabled in AION-082. `activation_ready` remains false, and
all activation paths stop at `activation_blocked_by_default`.

## Code Loading Remains Disabled

Code loading remains disabled. Module packages are not loaded, imported,
installed, mounted, executed, or routed by AION-082.

## External Sources Remain Disabled

External sources remain disabled for module strategy work. Manifests may
describe future source posture, but AION-082 does not download packages, clone
repositories, call external services, or install dependencies.

## First Module Strategy

The first governed module class is Generic Knowledge Intelligence. It is
selected because it demonstrates useful module review without tool execution,
external actions, controlled handoff, dynamic routes, package installation, or
runtime activation.

## Risk Ordering

1. Knowledge Intelligence.
2. Developer Assistance.
3. Operations Review.
4. Business Workflow Review.
5. Infrastructure Planning.
6. High-side-effect Regulated Workflow.

The first module must be low or medium risk. High or critical module classes
are post-design only.

## Branch Strategy

Post-v0.1 work uses feature branches. Module work uses separate module
branches. Main remains stable, and Brain core changes require architecture
review.

## Release Strategy

Every module release must pass manifest validation, extension intake, binding
validation, conformance, readiness, RC gate, freeze gate, no-domain drift,
boundary check, and docs audit.

## Governance Gates

No future module may bypass policy, audit, provenance, action proposal broker,
prompt governance, model output governance, tool intent blocker, sandbox
requirements, release/freeze gates, or operator review.

## Operator Review

Operator review is mandatory before any future activation request can be
considered. Review records must include declared capabilities, risk level,
scope, policy actions, sandbox posture, conformance result, readiness result,
and rollback plan.

## Future Activation Milestones

- AION-083: metadata-only activation request gate, still disabled.
- AION-084: Generic Knowledge Intelligence metadata package.
- AION-085: non-executing deterministic module mock runtime.
- AION-086: model provider adapter hardening.
- AION-087: operator UI decision.

## No-Go Rules

- No activation in AION-082 or AION-083.
- No code loading.
- No package installation.
- No dynamic route registration.
- No external calls.
- No full autonomy.
- No controlled action handoff.
- No production deployment logic.
- No domain module implementation in Brain core.
