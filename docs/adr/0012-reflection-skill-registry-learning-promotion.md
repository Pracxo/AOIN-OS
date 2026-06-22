# ADR 0012: Reflection Engine, Skill Registry, and Learning Promotion Gates

## Status

Accepted for AION Brain v0.1.

## Context

AION Brain already records decision traces, deterministic evaluations, learning
signals, and visual telemetry. The next learning layer needs a controlled path
from observed outcomes to reusable procedural memory without creating
uncontrolled self-modification.

## Decision

Add a Reflection Engine and Skill Registry.

Reflections convert evaluated traces, task runs, retrieval results, reasoning
runs, and execution outcomes into deterministic `ReflectionRecord` data.
Reflections may create `SkillCandidate` records when generic evidence supports
a reusable procedure.

Skills are data records, not generated code. They store trigger patterns,
preconditions, procedure steps, expected outcomes, risk level, status, owner
scope, metadata, and versions. They do not store executable source, shell
commands, dynamic Python, provider calls, or domain-specific workflows.

There is no auto-promotion. Skill candidates require explicit review and an
explicit promotion request. Promotion requires policy through `skill.promote`.
Activation requires policy through `skill.activate`; high and critical risk
activation requires approval.

`/brain/think` may create a reflection only when the event payload explicitly
sets `reflect: true`. It may create a skill candidate only when the payload also
sets `create_skill_candidate: true`. It must never promote or activate a skill.

## Consequences

AION can begin learning procedural patterns while keeping the Brain core
auditable, deterministic, and domain-neutral.

The planner may receive matched active skills as metadata, but it does not
execute skill procedure steps. The Retrieval Router may expose active skills as
procedural memory, but retrieval is recall, not truth or execution.

Future optimizers can improve candidate generation behind adapter boundaries,
but promotion, versioning, activation, audit, telemetry, and policy remain
AION-owned.
