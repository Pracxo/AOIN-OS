# Situation Model and Temporal State

AION Situation Model is the backend projection of current generic Brain state.
It answers what is currently active, stale, blocked, or closed without claiming
that projected state is external truth.

## Concepts

- `SituationRecord`: a scoped projection such as a general situation, dialogue
  situation, goal situation, task situation, workflow situation, operator review,
  replay, incident, or maintenance state.
- `StateAtom`: one projected observation from a source record. It stores source,
  predicate, value, status, confidence, sensitivity, scope, and refs.
- `StateTransition`: deterministic change detection between atoms.
- `TemporalStateWindow`: a bounded recent/session/focus/trace/daily/custom
  window over atoms, events, and situations.
- `ContextContinuityRecord`: carried and dropped references across turns,
  focus shifts, task resumes, workflow resumes, reviews, or replays.

## Rules

- Situation projection does not mutate events, goals, tasks, workflows,
  dialogue, memories, beliefs, entities, evidence, or operator records.
- Dry-run projection returns contracts and persists nothing.
- Controlled projection persists projection records only.
- State atoms are recall and working state, not truth.
- Stale or contradicted atoms must surface as constraints.
- Metadata and values must not contain secrets.
- AION Brain core remains domain-neutral.

## API

- `POST /brain/situations`
- `GET /brain/situations/{situation_id}`
- `POST /brain/situations/query`
- `POST /brain/situations/{situation_id}/close`
- `POST /brain/situations/state-atoms`
- `GET /brain/situations/state-atoms/{state_atom_id}`
- `GET /brain/situations/state-atoms`
- `POST /brain/situations/project`
- `GET /brain/situations/projection-runs/{projection_run_id}`
- `GET /brain/situations/transitions`
- `POST /brain/situations/temporal-windows`
- `GET /brain/situations/temporal-windows/{temporal_window_id}`
- `GET /brain/situations/temporal-windows`
- `POST /brain/situations/continuity`
- `GET /brain/situations/continuity`
