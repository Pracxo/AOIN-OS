# 0103: Connector Sandbox Design

## Status

Accepted

## Context

AION already has disabled connector runtime evidence, synthetic connector
simulation, and a connector policy action catalog. The next step needs a
connector sandbox design boundary and readiness gate so future sandbox work has
explicit isolation, capability, audit, provenance, and no-go rules before any
runtime exists.

## Decision

Add connector sandbox contracts, design services, isolation boundary service,
capability rules, denial service, readiness gate, query/status helpers, API
router, SDK resource, CLI preview commands, visual telemetry events, release
package evidence, freeze and hardening checks, docs, examples, static console
demo data, and no-go regression scripts.

The implementation remains local, read-only, and design-only. It does not add
real sandbox execution, filesystem access, network access, credential access,
token access, process spawning, dynamic imports, package installation,
connector activation, route registration, connector/provider SDKs, external
calls, package files, migrations, production auth, tool execution, or write
paths.

## Consequences

Future connector sandbox runtime work must replace this boundary through an
explicit later milestone. Until then, denied sandbox capabilities remain
visible to operators but unavailable in runtime and unavailable in dry-run
execution.
