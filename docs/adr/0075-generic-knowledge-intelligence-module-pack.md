# ADR 0075: Generic Knowledge Intelligence Module Pack

## Status

Accepted

## Context

AION Brain v0.1.0 is frozen and tagged. Post-v0.1 module work needs a concrete
example path through existing governance gates without changing Brain core or
activating runtime behavior.

## Decision

Create the first post-v0.1 metadata-only module pack.

Select Generic Knowledge Intelligence as the first governed module package.

The module remains metadata-only. It does not load code, install packages,
activate capabilities, register routes, register runtime surfaces, call
external services, or execute tools.

The activation gate must produce safe blockers. Expected blockers include
activation disabled, runtime registration disabled, dynamic route registration
disabled, and code loading disabled.

## Reason

AION needs to prove the post-v0.1 module lifecycle without runtime activation
risk. A generic knowledge module has low-to-medium risk because it is centered
on retrieval, summary, grounding, explanation, and answer contracts, and it has
no tool execution or external action requirement.

## Consequences

Future modules have a concrete example path through Brain gates:

`manifest -> intake -> slot -> binding -> validation -> conformance -> readiness -> activation request -> activation blocker -> operator review`

Operators can inspect fixtures, run offline validation, and review expected
blockers before any future activation design exists.

## Constraints

- No external calls.
- No runtime activation.
- No domain-specific implementation.
- No Brain core modification.
- No database tables.
- No API routes.
- No SDK resources.
- No CLI commands.
- Do not move, delete, or recreate the `aion-v0.1.0` tag.
