# ADR 0026: Autonomy Governor Operating Modes

## Status

Accepted for AION Brain v0.1.

## Decision

AION Brain adds a backend Autonomy Governor that resolves each requested action
against generic operating modes, risk ceilings, active profiles, temporary run
levels, delegation grants, approval state, and policy decisions.

The supported operating modes are:

- `disabled`
- `observe`
- `assist`
- `plan_only`
- `dry_run`
- `supervised_controlled`
- `delegated_controlled`

The default profile is conservative: `assist` by default, `dry_run` maximum,
`medium` maximum risk, and no external models, external tools, scheduler,
background worker, skill promotion, or memory forgetting permission unless
explicitly enabled.

## Reason

AION needs a reusable control plane before connecting stronger reasoning,
external capabilities, background workflows, and long-running work. The
governor gives the Brain one generic place to decide whether an action may
continue without embedding autonomy rules inside modules or execution systems.

## Consequences

Execution, durable workflows, scheduler ticks, worker ticks, task runs, model
gateway completion, MCP invocation, capability runtime invocation, skill
activation, memory forgetting, and the Brain loop all consult the Autonomy
Governor. Denials fail closed and return structured blocked results.

Autonomy lifecycle records can feed audit and visual telemetry. Future modules
can request higher modes, but they cannot self-authorize them.

## Constraints

- No full autonomy is enabled by default.
- Policy remains mandatory for autonomy changes and decisions.
- Delegated controlled operation requires an active scoped delegation.
- External model/tool use requires explicit profile gates.
- No domain-specific autonomy logic is allowed in Brain core.
- No external calls are introduced by the Autonomy Governor in v0.1.
