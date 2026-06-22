# Module Risk Classification

## Purpose

Module risk classification determines how much policy, sandbox, approval,
operator review, and release evidence a future module needs.

## Risk Levels

- `low`: metadata-only or read-oriented behavior with no external action and
  limited scoped data access.
- `medium`: broader retrieval, summarization, planning, or explanation with
  meaningful review needs but no direct side effects.
- `high`: any future module that may trigger tools, external calls, broad data
  access, complex policy, or difficult rollback.
- `critical`: any future module with high side effects, difficult reversal, or
  strict operational impact.

## Criteria

- Side-effect scope.
- Data access.
- Tool execution.
- External calls.
- Autonomy level.
- Sandbox need.
- Policy complexity.
- Audit burden.
- Rollback complexity.

## First Module Rule

The first module must be low or medium risk.

High or critical modules require future activation design and explicit
operator approval.

High-side-effect modules are post-design only.

## Generic Knowledge Intelligence Classification

Generic Knowledge Intelligence is low-to-medium risk in metadata-only form.
The selected capabilities are read, summarize, ground, explain, and answer
contracts. They do not execute tools, call external services, register routes,
mutate runtime configuration, request controlled handoff, or load code.

`generic.knowledge.retrieve`, `generic.knowledge.summarize`, and
`generic.knowledge.explain` are low risk. `generic.knowledge.ground` and
`generic.knowledge.answer` are medium risk because they depend on reviewable
context, grounding, and uncertainty constraints.
