# 0051: Experience Ledger and Learning Synthesis

## Status

Accepted

## Context

AION Brain can record outcomes, verification results, feedback, traces,
regressions, replay drift, decisions, and operator signals. The Brain needs a
generic way to remember what happened and synthesize reviewable learning
material without changing behavior automatically.

## Decision

Add a generic Experience Ledger and deterministic Learning Synthesizer.

AION owns these contracts:

- `ExperienceRecord`
- `LearningPattern`
- `LessonRecord`
- `LearningSynthesisRun`
- `PatternMiningRun`
- `SkillCandidateSuggestion`
- `RegressionCandidateSuggestion`

Pattern mining groups generic experiences using deterministic lexical rules,
minimum frequency, and minimum confidence. Learning synthesis can run as
`dry_run` or `controlled`. Controlled mode may persist review records, but it
does not promote skills, create active skill records, create regression cases,
modify code, execute remediation, call model providers, or call external
services.

## Consequences

Future modules can query reviewable learning material through public Brain
contracts. Operator Control Tower can surface high-severity patterns and open
suggestions. Visual telemetry can project experience, pattern, lesson, and
suggestion nodes.

The Experience Ledger is not a replacement for source records. It is a generic
learning input ledger with provenance references.

## Constraints

- Brain core remains domain-neutral.
- Source records are not mutated by learning synthesis.
- Skill promotion stays outside AION-057 and must remain separately governed.
- Regression case creation stays outside AION-057 and must remain separately
  governed.
- No external intelligence repositories, model providers, or observability
  services are called.
