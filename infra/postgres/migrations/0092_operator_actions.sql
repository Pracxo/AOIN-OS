CREATE TABLE IF NOT EXISTS aion_operator_action_requests (
  operator_action_request_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  action_key TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  risk_level TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  request_payload_hash TEXT NOT NULL,
  redacted_request_payload JSONB NOT NULL,
  required_policy_actions JSONB NOT NULL,
  required_approvals JSONB NOT NULL,
  required_evidence_refs JSONB NOT NULL,
  blocker_refs JSONB NOT NULL,
  preview_id TEXT NULL,
  review_id TEXT NULL,
  execution_allowed BOOLEAN NOT NULL,
  external_calls_allowed BOOLEAN NOT NULL,
  activation_allowed BOOLEAN NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ NULL,
  archived_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_trace_id
  ON aion_operator_action_requests (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_actor_id
  ON aion_operator_action_requests (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_workspace_id
  ON aion_operator_action_requests (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_action_key
  ON aion_operator_action_requests (action_key);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_action_type
  ON aion_operator_action_requests (action_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_target_type
  ON aion_operator_action_requests (target_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_status
  ON aion_operator_action_requests (status);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_mode
  ON aion_operator_action_requests (mode);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_risk_level
  ON aion_operator_action_requests (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_execution_allowed
  ON aion_operator_action_requests (execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_external_calls_allowed
  ON aion_operator_action_requests (external_calls_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_activation_allowed
  ON aion_operator_action_requests (activation_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_created_at
  ON aion_operator_action_requests (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_requests_deleted_at
  ON aion_operator_action_requests (deleted_at);

CREATE TABLE IF NOT EXISTS aion_operator_action_previews (
  operator_action_preview_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  operator_action_request_id TEXT NOT NULL,
  status TEXT NOT NULL,
  preview_type TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  expected_effects JSONB NOT NULL,
  blocked_effects JSONB NOT NULL,
  dry_run_result JSONB NOT NULL,
  would_execute BOOLEAN NOT NULL,
  execution_allowed BOOLEAN NOT NULL,
  external_calls_allowed BOOLEAN NOT NULL,
  activation_allowed BOOLEAN NOT NULL,
  blockers JSONB NOT NULL,
  warnings JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_trace_id
  ON aion_operator_action_previews (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_request_id
  ON aion_operator_action_previews (operator_action_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_status
  ON aion_operator_action_previews (status);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_preview_type
  ON aion_operator_action_previews (preview_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_would_execute
  ON aion_operator_action_previews (would_execute);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_execution_allowed
  ON aion_operator_action_previews (execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_external_calls_allowed
  ON aion_operator_action_previews (external_calls_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_activation_allowed
  ON aion_operator_action_previews (activation_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_previews_created_at
  ON aion_operator_action_previews (created_at);

CREATE TABLE IF NOT EXISTS aion_operator_action_blockers (
  operator_action_blocker_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  operator_action_request_id TEXT NULL,
  blocker_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  source_type TEXT NULL,
  source_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL,
  dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_trace_id
  ON aion_operator_action_blockers (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_request_id
  ON aion_operator_action_blockers (operator_action_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_blocker_type
  ON aion_operator_action_blockers (blocker_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_severity
  ON aion_operator_action_blockers (severity);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_status
  ON aion_operator_action_blockers (status);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_source_type
  ON aion_operator_action_blockers (source_type);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_source_id
  ON aion_operator_action_blockers (source_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_blockers_created_at
  ON aion_operator_action_blockers (created_at);

CREATE TABLE IF NOT EXISTS aion_operator_action_reviews (
  operator_action_review_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  operator_action_request_id TEXT NOT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  reviewer_id TEXT NULL,
  status TEXT NOT NULL,
  decision TEXT NOT NULL,
  reason TEXT NOT NULL,
  approval_present BOOLEAN NOT NULL,
  execution_allowed BOOLEAN NOT NULL,
  blocker_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_trace_id
  ON aion_operator_action_reviews (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_request_id
  ON aion_operator_action_reviews (operator_action_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_actor_id
  ON aion_operator_action_reviews (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_workspace_id
  ON aion_operator_action_reviews (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_reviewer_id
  ON aion_operator_action_reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_status
  ON aion_operator_action_reviews (status);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_decision
  ON aion_operator_action_reviews (decision);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_execution_allowed
  ON aion_operator_action_reviews (execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_operator_action_reviews_created_at
  ON aion_operator_action_reviews (created_at);
