CREATE TABLE IF NOT EXISTS aion_dialogue_sessions (
  dialogue_session_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  session_type TEXT NOT NULL,
  title TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  active_focus_session_id TEXT NULL,
  active_goal_id TEXT NULL,
  active_task_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_trace_id ON aion_dialogue_sessions(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_actor_id ON aion_dialogue_sessions(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_workspace_id ON aion_dialogue_sessions(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_status ON aion_dialogue_sessions(status);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_session_type ON aion_dialogue_sessions(session_type);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_active_focus_session_id ON aion_dialogue_sessions(active_focus_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_active_goal_id ON aion_dialogue_sessions(active_goal_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_active_task_id ON aion_dialogue_sessions(active_task_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_sessions_created_at ON aion_dialogue_sessions(created_at);

CREATE TABLE IF NOT EXISTS aion_dialogue_messages (
  message_id TEXT PRIMARY KEY,
  dialogue_session_id TEXT NOT NULL REFERENCES aion_dialogue_sessions(dialogue_session_id),
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  role TEXT NOT NULL,
  message_type TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  content_redacted BOOLEAN NOT NULL,
  grounding_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  response_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_dialogue_session_id ON aion_dialogue_messages(dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_trace_id ON aion_dialogue_messages(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_actor_id ON aion_dialogue_messages(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_workspace_id ON aion_dialogue_messages(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_role ON aion_dialogue_messages(role);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_message_type ON aion_dialogue_messages(message_type);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_content_hash ON aion_dialogue_messages(content_hash);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_created_at ON aion_dialogue_messages(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_messages_deleted_at ON aion_dialogue_messages(deleted_at);

CREATE TABLE IF NOT EXISTS aion_clarification_requests (
  clarification_id TEXT PRIMARY KEY,
  dialogue_session_id TEXT NULL,
  message_id TEXT NULL,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  question TEXT NOT NULL,
  reason TEXT NOT NULL,
  required BOOLEAN NOT NULL,
  answer_message_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  answered_at TIMESTAMPTZ NULL,
  cancelled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_clarification_requests_dialogue_session_id ON aion_clarification_requests(dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_clarification_requests_message_id ON aion_clarification_requests(message_id);
CREATE INDEX IF NOT EXISTS ix_aion_clarification_requests_trace_id ON aion_clarification_requests(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_clarification_requests_status ON aion_clarification_requests(status);
CREATE INDEX IF NOT EXISTS ix_aion_clarification_requests_required ON aion_clarification_requests(required);
CREATE INDEX IF NOT EXISTS ix_aion_clarification_requests_created_at ON aion_clarification_requests(created_at);

CREATE TABLE IF NOT EXISTS aion_response_drafts (
  response_id TEXT PRIMARY KEY,
  dialogue_session_id TEXT NULL,
  message_id TEXT NULL,
  trace_id TEXT NULL,
  reasoning_id TEXT NULL,
  plan_id TEXT NULL,
  status TEXT NOT NULL,
  response_type TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  grounded BOOLEAN NOT NULL,
  grounding_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  clarification_refs JSONB NOT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_dialogue_session_id ON aion_response_drafts(dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_message_id ON aion_response_drafts(message_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_trace_id ON aion_response_drafts(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_reasoning_id ON aion_response_drafts(reasoning_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_plan_id ON aion_response_drafts(plan_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_status ON aion_response_drafts(status);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_response_type ON aion_response_drafts(response_type);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_grounded ON aion_response_drafts(grounded);
CREATE INDEX IF NOT EXISTS ix_aion_response_drafts_created_at ON aion_response_drafts(created_at);

CREATE TABLE IF NOT EXISTS aion_response_verifications (
  verification_id TEXT PRIMARY KEY,
  response_id TEXT NOT NULL REFERENCES aion_response_drafts(response_id),
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  grounded BOOLEAN NOT NULL,
  policy_ok BOOLEAN NOT NULL,
  autonomy_ok BOOLEAN NOT NULL,
  approval_required BOOLEAN NOT NULL,
  issues JSONB NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_response_id ON aion_response_verifications(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_trace_id ON aion_response_verifications(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_status ON aion_response_verifications(status);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_grounded ON aion_response_verifications(grounded);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_policy_ok ON aion_response_verifications(policy_ok);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_autonomy_ok ON aion_response_verifications(autonomy_ok);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_approval_required ON aion_response_verifications(approval_required);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_score ON aion_response_verifications(score);
CREATE INDEX IF NOT EXISTS ix_aion_response_verifications_created_at ON aion_response_verifications(created_at);

CREATE TABLE IF NOT EXISTS aion_response_delivery_records (
  delivery_id TEXT PRIMARY KEY,
  response_id TEXT NOT NULL REFERENCES aion_response_drafts(response_id),
  dialogue_session_id TEXT NULL,
  trace_id TEXT NULL,
  delivery_type TEXT NOT NULL,
  status TEXT NOT NULL,
  delivered_to TEXT NULL,
  output_channel TEXT NOT NULL,
  payload JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_response_id ON aion_response_delivery_records(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_dialogue_session_id ON aion_response_delivery_records(dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_trace_id ON aion_response_delivery_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_delivery_type ON aion_response_delivery_records(delivery_type);
CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_status ON aion_response_delivery_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_output_channel ON aion_response_delivery_records(output_channel);
CREATE INDEX IF NOT EXISTS ix_aion_response_delivery_records_created_at ON aion_response_delivery_records(created_at);

CREATE TABLE IF NOT EXISTS aion_dialogue_feedback (
  feedback_id TEXT PRIMARY KEY,
  dialogue_session_id TEXT NULL,
  message_id TEXT NULL,
  response_id TEXT NULL,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  feedback_type TEXT NOT NULL,
  rating INTEGER NULL,
  comment TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_dialogue_session_id ON aion_dialogue_feedback(dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_message_id ON aion_dialogue_feedback(message_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_response_id ON aion_dialogue_feedback(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_trace_id ON aion_dialogue_feedback(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_actor_id ON aion_dialogue_feedback(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_feedback_type ON aion_dialogue_feedback(feedback_type);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_rating ON aion_dialogue_feedback(rating);
CREATE INDEX IF NOT EXISTS ix_aion_dialogue_feedback_created_at ON aion_dialogue_feedback(created_at);
