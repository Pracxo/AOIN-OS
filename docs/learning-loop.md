# Learning Loop

AION Brain v0.1 learns through evaluated traces. The runtime creates a
`DecisionTrace`, the evaluator creates an `EvaluationRecord`, and the learning
engine turns that pair into a candidate `LearningSignal`.

All learning signals remain `promotion_status: candidate` in v0.1. The Brain
never auto-promotes a signal, never modifies core code, and never turns a
candidate into operational behavior without a later governed promotion path.

The next governed layer is:

```text
LearningSignal -> ReflectionRecord -> SkillCandidate -> reviewed promotion -> SkillRecord
```

Learning signals feed the Reflection Engine. Reflections may identify generic
observations, proposed procedural changes, and risks. Reflections may create
skill candidates only when deterministic evidence supports a reusable generic
procedure.

Skill candidates require review. Promotion requires policy through
`skill.promote`. Activation requires policy through `skill.activate`, and high
or critical risk activation requires approval. Draft skills are not retrieved
or used by the planner as active procedural memory.

The approval control plane records review evidence only. An approved skill
promotion or activation request does not mutate behavior automatically; the
caller must submit the governed promotion or activation request with approval
evidence. Learning remains a candidate path until policy, guardrails, and
approval checks all allow the transition.

The Brain core stays domain-neutral. Learning types are generic candidates such
as retrieval improvement, planning patterns, policy feedback, capability
selection, user preference, and failure patterns. Domain-specific learning lives
outside Brain core.

Evaluation is deterministic and does not use LLM grading. Scores are bounded
between 0 and 1 and describe goal completion, context quality, memory relevance,
plan quality, policy compliance, execution readiness, and lifecycle readiness.

Execution outcomes can produce learning candidates. Completed generic execution
supports `planning_pattern_candidate`; failed or policy-blocked execution
supports `failure_pattern_candidate`. These signals still remain candidates and
are never auto-promoted in v0.1.

Lifecycle outcomes can also produce candidate signals. A trace that can be
converted into a task receives the `plan_can_be_converted_to_task` lesson. A
failed or policy-blocked task run can become a `failure_pattern_candidate`, and
a repeated task pattern can become a `planning_pattern_candidate`. These remain
observations only; AION Brain does not auto-create future workflows or promote
learning into behavior in v0.1.

Durable workflow outcomes can inform future learning signals, but they do not
create new workflow definitions, start workers, schedule retries outside the
explicit workflow engine, or promote a pattern into behavior automatically.
Workflow definitions and workflow runs stay behind policy-gated APIs.

`/brain/think` can create a reflection only when the event payload contains
`reflect: true`. It can create a skill candidate only when the payload also
contains `create_skill_candidate: true`. It never promotes or activates a skill.

Skills are procedural memory records, not executable code. The learning loop
does not write source files, dynamically execute Python, run shell commands,
call external AI services, fine-tune models, or create domain-specific
procedures in Brain core.

## Replay-Informed Learning

Golden traces protect core Brain behavior by making deterministic outcomes
reproducible. Regression drift can inform future learning signals, but v0.1
replay does not promote skills, modify code, create external side effects, or
turn drift into behavior automatically.

Replay may persist a local learning signal marked as replay-derived. That
signal remains a candidate under the same governed learning rules as every
other signal.

## Outcome Feedback Bridge

Outcome feedback gives the learning loop verified or failed effect context.
The bridge reads `OutcomeRecord` status, effect verification metadata, and
causal attribution references, then creates reviewable `OutcomeFeedback`.

Dry-run bridge calls do not persist feedback. Controlled bridge calls may
persist feedback and candidate learning metadata only. They do not promote
skills, activate procedures, rewrite memories, retry commands, create
workflows, call model providers, or call external services.

Failed, partial, contradicted, and verified outcomes can become learning
signals, but every signal remains a candidate until a later governed promotion
path explicitly approves it.

## Experience Ledger

AION-057 adds `ExperienceRecord` as the generic observed-experience contract.
The ledger can reference outcomes, decisions, commands, workflows, regressions,
replays, audit records, signals, and generic manual sources. Experience records
hold a title, summary, owner scope, score, confidence, observed timestamp, and
safe metadata.

The ledger is canonical for learning synthesis input. Source records remain
canonical for their own lifecycle and are not mutated by learning synthesis.

## Pattern Mining

Pattern mining is deterministic in v0.1. It groups experiences by generic
experience type, source type, and a normalized lexical summary key. It then
applies minimum frequency and confidence thresholds. No embeddings, LLM calls,
semantic clustering, external repos, or domain-specific classifiers are used.

Patterns are review material only. They can produce lessons, passive skill
candidate suggestions, and passive regression candidate suggestions.

## Lesson Records and Suggestions

`LessonRecord` stores a generic lesson derived from a pattern. Lessons are
recall and review aids, not executable behavior.

`SkillCandidateSuggestion` is not a `SkillRecord`. It may be accepted, rejected,
or converted into a passive candidate reference, but AION-057 does not promote
or activate skills.

`RegressionCandidateSuggestion` is not a regression case. It may be accepted or
rejected, but AION-057 does not create executable regression tests.

## Synthesis Modes

`dry_run` synthesis returns proposed experiences, patterns, lessons, and
suggestions without persisting generated learning material beyond the run
record. `controlled` synthesis persists review records but still does not
execute actions, mutate source records, call model providers, call external
services, or write source code.

Auto synthesis is disabled by default through
`AION_LEARNING_AUTO_SYNTHESIS_ENABLED=false`.
