# 0066: Extension Registry and Module Intake

## Status

Accepted.

## Context

AION needs a way to understand future modules before it can safely load,
activate, install, or execute anything from them. Previous milestones defined
contracts, policy gates, sandbox boundaries, runtime configuration, release
readiness, operator visibility, and interface drift checks. The next safe step
is a registry that stores extension metadata and compatibility records only.

## Decision

Add a Brain-owned Extension Registry and Module Intake layer for metadata-only
manifests. The registry owns package records, capability declarations,
dependency declarations, compatibility runs, intake runs, reviews, and future
install plans.

The registry does not load extension code, install dependencies, run shell
commands, clone repositories, call external services, register dynamic routes,
register active capabilities, or activate policy actions from manifests.

Compatibility checks are deterministic and local. They evaluate generic
metadata against AION-owned contracts, runtime configuration, policy catalog,
sandbox posture, security baseline, release/freeze gates, and registry
constraints.

Install plans are records only in v0.1. They must keep `executable=false` and
`execution_allowed=false`.

## Consequences

Future modules can publish manifests that AION can validate, query, review,
and display without running them. Operator, release, freeze, security,
resource registry, SDK, CLI, and visual telemetry surfaces can reason about
extension readiness without expanding the execution boundary.

The cost is that v0.1 cannot install or activate extensions. That is
intentional; execution requires separate policy, sandbox, approval, and runtime
tasks.

## Constraints

- AION public contracts remain independent of third-party module internals.
- Manifests are generic and domain-neutral.
- Extension intake is policy-gated.
- Extension code loading, activation, and external sources are disabled by
  default.
- Extension Registry services must not call external networks or package
  managers.
- No frontend code is introduced by this task.
