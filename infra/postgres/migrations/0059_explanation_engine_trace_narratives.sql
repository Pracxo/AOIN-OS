CREATE TABLE IF NOT EXISTS aion_explanation_records (
  explanation_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  explanation_type TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  grounded BOOLEAN NOT NULL,
  evidence_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  belief_refs JSONB NOT NULL,
  decision_refs JSONB NOT NULL,
  outcome_refs JSONB NOT NULL,
  audit_refs JSONB NOT NULL,
  provenance_refs JSONB NOT NULL,
  policy_decision_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  approval_request_id TEXT NULL,
  redaction_metadata JSONB NOT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_trace_id ON aion_explanation_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_actor_id ON aion_explanation_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_workspace_id ON aion_explanation_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_explanation_type ON aion_explanation_records(explanation_type);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_target_type ON aion_explanation_records(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_target_id ON aion_explanation_records(target_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_status ON aion_explanation_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_confidence ON aion_explanation_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_grounded ON aion_explanation_records(grounded);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_records_created_at ON aion_explanation_records(created_at);

CREATE TABLE IF NOT EXISTS aion_explanation_steps (
  explanation_step_id TEXT PRIMARY KEY,
  explanation_id TEXT NOT NULL REFERENCES aion_explanation_records(explanation_id),
  step_order INTEGER NOT NULL,
  step_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  source_type TEXT NULL,
  source_id TEXT NULL,
  refs JSONB NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_explanation_id ON aion_explanation_steps(explanation_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_step_order ON aion_explanation_steps(step_order);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_step_type ON aion_explanation_steps(step_type);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_source_type ON aion_explanation_steps(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_source_id ON aion_explanation_steps(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_confidence ON aion_explanation_steps(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_steps_created_at ON aion_explanation_steps(created_at);

CREATE TABLE IF NOT EXISTS aion_trace_narratives (
  trace_narrative_id TEXT PRIMARY KEY,
  trace_id TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  timeline JSONB NOT NULL,
  key_decisions JSONB NOT NULL,
  blockers JSONB NOT NULL,
  approvals JSONB NOT NULL,
  outcomes JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  audit_refs JSONB NOT NULL,
  redaction_metadata JSONB NOT NULL,
  metadata JSONB NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_trace_narratives_trace_id ON aion_trace_narratives(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_trace_narratives_status ON aion_trace_narratives(status);
CREATE INDEX IF NOT EXISTS ix_aion_trace_narratives_confidence ON aion_trace_narratives(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_trace_narratives_created_at ON aion_trace_narratives(created_at);

CREATE TABLE IF NOT EXISTS aion_why_not_records (
  why_not_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  question TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NULL,
  requested_action TEXT NULL,
  answer TEXT NOT NULL,
  blockers JSONB NOT NULL,
  missing_requirements JSONB NOT NULL,
  next_possible_steps JSONB NOT NULL,
  refs JSONB NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_trace_id ON aion_why_not_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_actor_id ON aion_why_not_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_workspace_id ON aion_why_not_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_target_type ON aion_why_not_records(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_target_id ON aion_why_not_records(target_id);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_requested_action ON aion_why_not_records(requested_action);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_confidence ON aion_why_not_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_why_not_records_created_at ON aion_why_not_records(created_at);

CREATE TABLE IF NOT EXISTS aion_explanation_feedback (
  explanation_feedback_id TEXT PRIMARY KEY,
  explanation_id TEXT NULL,
  trace_narrative_id TEXT NULL,
  why_not_id TEXT NULL,
  actor_id TEXT NULL,
  feedback_type TEXT NOT NULL,
  rating INTEGER NULL,
  comment TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_explanation_id ON aion_explanation_feedback(explanation_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_trace_narrative_id ON aion_explanation_feedback(trace_narrative_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_why_not_id ON aion_explanation_feedback(why_not_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_actor_id ON aion_explanation_feedback(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_feedback_type ON aion_explanation_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_rating ON aion_explanation_feedback(rating);
CREATE INDEX IF NOT EXISTS ix_aion_explanation_feedback_created_at ON aion_explanation_feedback(created_at);
