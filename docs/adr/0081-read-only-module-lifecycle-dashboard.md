# ADR 0081: Read-Only Module Lifecycle Dashboard

## Status

Accepted.

## Context

AION-089 created a static local Operator Console prototype. The next operator
need is visibility into the module lifecycle path, especially the Generic
Knowledge Intelligence trail and its expected activation blockers.

## Decision

Add a read-only Module Lifecycle Dashboard to the static console prototype.

Generic Knowledge Intelligence is the first trail shown.

The dashboard is read-only and static.

Activation remains blocked.

No frontend dependencies are added.

## Reason

Operators need a visible module lifecycle trail before any real UI or
activation work. The static dashboard lets AION validate review structure,
evidence refs, blockers, and mock runtime interpretation without expanding the
runtime surface.

## Consequences

Future module console views can reuse this lifecycle structure.

The dashboard can be replaced later by an approved UI while keeping the same
read-only evidence model.

The static console still owns no backend state and no activation authority.

## Constraints

- no activation
- no writes
- no external calls
- no framework or build system
- no runtime route registration
- no code loading
- no package installation
- no protected data exposure
