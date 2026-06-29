# 0094: Static Console UX Refinement

## Status

Accepted

## Context

AION-089 through AION-102 established a static local Operator Console and
stabilized its no-go gates. Operators now need clearer navigation,
accessibility, and information architecture before any later UI implementation
can be considered.

## Decision

Refine the static console UX without adding frontend dependencies.

Navigation remains static and local. View grouping, section shortcuts, and the
safety blocker view run entirely in the existing static JavaScript.

Safe command copy is allowed for local read-only checks only. The allowlist is
limited to UI release, static safety, operator-platform regression,
operator-platform freeze, and docs checks.

No write, activation, execution, provider, auth, credential, token, cookie, or
session controls are added.

## Reason

Operators need clearer navigation and accessibility before any future UI
implementation. The static prototype can prove the information architecture
without introducing a framework, backend runtime, or privileged control.

## Consequences

Future UI work can inherit the static information architecture, navigation
groups, safety footer, local command rules, and accessibility checklist.

AION-103 remains a polish and evidence milestone. It does not claim production
UI readiness.

## Constraints

- No frontend framework.
- No external calls.
- No privileged controls.
- No production UI claim.
- No package files, lockfiles, build tooling, migrations, API routes, SDK
  resources, or CLI command implementations.
