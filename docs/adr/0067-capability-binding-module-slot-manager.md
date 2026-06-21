# 0067: Capability Binding Registry and Module Slot Manager

## Status

Accepted.

## Context

AION can now intake extension manifests as metadata. It still needs a governed
staging layer between extension package records and any future runtime
activation path. That layer must make future modules visible for review without
loading code, installing dependencies, registering routes, or activating
capabilities.

## Decision

Add a Brain-owned Capability Binding Registry and Module Slot Manager.

Module slots are metadata-only records for future modules. Capability bindings
are inactive mappings from a module slot to declared capability metadata. They
do not activate capabilities or register them with the active Capability
Registry.

Route binding previews describe future route shapes only. They do not register
routes. Mount plans describe future mount requirements only. They do not
install, mount, or execute anything.

Binding validation is deterministic and local. It checks declared contracts,
policy actions, settings, sandbox requirements, route-registration flags, and
activation flags before a binding can be considered ready for later review.

## Consequences

Future modules can be reviewed, bound, validated, planned, indexed, summarized,
and shown to operators before runtime activation exists. Release, freeze,
security, resource registry, audit, provenance, SDK, CLI, and visual telemetry
surfaces can reason about staged module readiness without expanding the
execution boundary.

The cost is that v0.1 still cannot load, install, activate, execute, or route
extension code. That is intentional; those capabilities require separate
runtime, sandbox, policy, and approval milestones.

## Constraints

- No code loading.
- No package installation.
- No capability activation.
- No dynamic route registration.
- No runtime configuration mutation.
- No external service calls.
- No domain-specific module logic.
