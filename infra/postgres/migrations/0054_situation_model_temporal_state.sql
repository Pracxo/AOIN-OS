CREATE TABLE IF NOT EXISTS aion_situations (
  situation_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  situation_type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  active_goal_ids JSONB NOT NULL,
  active_task_ids JSONB NOT NULL,
  active_workflow_run_ids JSONB NOT NULL,
  active_focus_session_ids JSONB NOT NULL,
  entity_refs JSONB NOT NULL,
  belief_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  constraints JSONB NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_situations_trace_id ON aion_situations (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_situations_actor_id ON aion_situations (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_situations_workspace_id ON aion_situations (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_situations_status ON aion_situations (status);
CREATE INDEX IF NOT EXISTS ix_aion_situations_situation_type ON aion_situations (situation_type);
CREATE INDEX IF NOT EXISTS ix_aion_situations_confidence ON aion_situations (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_situations_created_at ON aion_situations (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_situations_updated_at ON aion_situations (updated_at);

CREATE TABLE IF NOT EXISTS aion_state_atoms (
  state_atom_id TEXT PRIMARY KEY,
  situation_id TEXT NULL,
  trace_id TEXT NULL,
  atom_type TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  subject_ref TEXT NULL,
  predicate TEXT NOT NULL,
  object_ref TEXT NULL,
  value JSONB NOT NULL,
  status TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  sensitivity TEXT NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  valid_from TIMESTAMPTZ NULL,
  valid_to TIMESTAMPTZ NULL,
  owner_scope JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  belief_refs JSONB NOT NULL,
  entity_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  superseded_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_situation_id ON aion_state_atoms (situation_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_trace_id ON aion_state_atoms (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_atom_type ON aion_state_atoms (atom_type);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_source_type_source_id ON aion_state_atoms (source_type, source_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_subject_ref ON aion_state_atoms (subject_ref);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_predicate ON aion_state_atoms (predicate);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_object_ref ON aion_state_atoms (object_ref);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_status ON aion_state_atoms (status);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_confidence ON aion_state_atoms (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_sensitivity ON aion_state_atoms (sensitivity);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_observed_at ON aion_state_atoms (observed_at);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_valid_from ON aion_state_atoms (valid_from);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_valid_to ON aion_state_atoms (valid_to);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_deleted_at ON aion_state_atoms (deleted_at);
CREATE INDEX IF NOT EXISTS ix_aion_state_atoms_created_at ON aion_state_atoms (created_at);

CREATE TABLE IF NOT EXISTS aion_temporal_state_windows (
  temporal_window_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  window_type TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  start_at TIMESTAMPTZ NOT NULL,
  end_at TIMESTAMPTZ NOT NULL,
  state_atom_ids JSONB NOT NULL,
  event_ids JSONB NOT NULL,
  situation_ids JSONB NOT NULL,
  summary TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_trace_id ON aion_temporal_state_windows (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_actor_id ON aion_temporal_state_windows (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_workspace_id ON aion_temporal_state_windows (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_window_type ON aion_temporal_state_windows (window_type);
CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_start_at ON aion_temporal_state_windows (start_at);
CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_end_at ON aion_temporal_state_windows (end_at);
CREATE INDEX IF NOT EXISTS ix_aion_temporal_windows_created_at ON aion_temporal_state_windows (created_at);

CREATE TABLE IF NOT EXISTS aion_situation_projection_runs (
  projection_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  input JSONB NOT NULL,
  situation_ids JSONB NOT NULL,
  state_atom_ids JSONB NOT NULL,
  transition_ids JSONB NOT NULL,
  warnings JSONB NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_projection_runs_trace_id ON aion_situation_projection_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_projection_runs_actor_id ON aion_situation_projection_runs (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_projection_runs_workspace_id ON aion_situation_projection_runs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_projection_runs_status ON aion_situation_projection_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_projection_runs_mode ON aion_situation_projection_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_projection_runs_created_at ON aion_situation_projection_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_state_transitions (
  state_transition_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  situation_id TEXT NULL,
  transition_type TEXT NOT NULL,
  from_state_atom_id TEXT NULL,
  to_state_atom_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  status TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  reason TEXT NOT NULL,
  evidence_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_trace_id ON aion_state_transitions (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_situation_id ON aion_state_transitions (situation_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_transition_type ON aion_state_transitions (transition_type);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_from_atom ON aion_state_transitions (from_state_atom_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_to_atom ON aion_state_transitions (to_state_atom_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_source_type_source_id ON aion_state_transitions (source_type, source_id);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_status ON aion_state_transitions (status);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_confidence ON aion_state_transitions (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_state_transitions_created_at ON aion_state_transitions (created_at);

CREATE TABLE IF NOT EXISTS aion_context_continuity_records (
  continuity_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  dialogue_session_id TEXT NULL,
  focus_session_id TEXT NULL,
  situation_id TEXT NULL,
  continuity_type TEXT NOT NULL,
  status TEXT NOT NULL,
  carried_refs JSONB NOT NULL,
  dropped_refs JSONB NOT NULL,
  constraints JSONB NOT NULL,
  reason TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_continuity_trace_id ON aion_context_continuity_records (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_actor_id ON aion_context_continuity_records (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_workspace_id ON aion_context_continuity_records (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_dialogue_session_id ON aion_context_continuity_records (dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_focus_session_id ON aion_context_continuity_records (focus_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_situation_id ON aion_context_continuity_records (situation_id);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_type ON aion_context_continuity_records (continuity_type);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_status ON aion_context_continuity_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_continuity_created_at ON aion_context_continuity_records (created_at);
