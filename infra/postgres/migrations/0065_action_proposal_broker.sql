CREATE TABLE IF NOT EXISTS aion_action_proposals (
  action_proposal_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  status TEXT NOT NULL,
  proposal_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  action_type TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  proposed_payload JSONB NOT NULL,
  required_permissions JSONB NOT NULL,
  required_approvals JSONB NOT NULL,
  risk_level TEXT NOT NULL,
  autonomy_mode_required TEXT NULL,
  sandbox_profile_id TEXT NULL,
  capability_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  decision_refs JSONB NOT NULL,
  model_output_refs JSONB NOT NULL,
  tool_intent_refs JSONB NOT NULL,
  blocker_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ NULL,
  archived_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_trace_id ON aion_action_proposals(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_actor_id ON aion_action_proposals(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_workspace_id ON aion_action_proposals(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_source_type ON aion_action_proposals(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_source_id ON aion_action_proposals(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_status ON aion_action_proposals(status);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_proposal_type ON aion_action_proposals(proposal_type);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_action_type ON aion_action_proposals(action_type);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_target_type ON aion_action_proposals(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_risk_level ON aion_action_proposals(risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_created_at ON aion_action_proposals(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_action_proposals_deleted_at ON aion_action_proposals(deleted_at);

CREATE TABLE IF NOT EXISTS aion_action_blockers (
  action_blocker_id TEXT PRIMARY KEY,
  action_proposal_id TEXT NULL,
  trace_id TEXT NULL,
  blocker_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  missing_requirement TEXT NULL,
  source_type TEXT NULL,
  source_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_action_proposal_id ON aion_action_blockers(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_trace_id ON aion_action_blockers(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_blocker_type ON aion_action_blockers(blocker_type);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_severity ON aion_action_blockers(severity);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_status ON aion_action_blockers(status);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_source_type ON aion_action_blockers(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_source_id ON aion_action_blockers(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_blockers_created_at ON aion_action_blockers(created_at);

CREATE TABLE IF NOT EXISTS aion_action_proposal_reviews (
  action_review_id TEXT PRIMARY KEY,
  action_proposal_id TEXT NOT NULL REFERENCES aion_action_proposals(action_proposal_id),
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  decision TEXT NOT NULL,
  reviewer_id TEXT NULL,
  reason TEXT NOT NULL,
  policy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  approval_request_id TEXT NULL,
  blocker_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_action_proposal_id ON aion_action_proposal_reviews(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_trace_id ON aion_action_proposal_reviews(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_actor_id ON aion_action_proposal_reviews(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_workspace_id ON aion_action_proposal_reviews(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_status ON aion_action_proposal_reviews(status);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_decision ON aion_action_proposal_reviews(decision);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_reviewer_id ON aion_action_proposal_reviews(reviewer_id);
CREATE INDEX IF NOT EXISTS ix_aion_action_reviews_created_at ON aion_action_proposal_reviews(created_at);

CREATE TABLE IF NOT EXISTS aion_execution_handoffs (
  execution_handoff_id TEXT PRIMARY KEY,
  action_proposal_id TEXT NOT NULL REFERENCES aion_action_proposals(action_proposal_id),
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  handoff_type TEXT NOT NULL,
  target_system TEXT NOT NULL,
  target_request_id TEXT NULL,
  target_run_id TEXT NULL,
  handoff_payload JSONB NOT NULL,
  policy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  approval_request_id TEXT NULL,
  blocker_refs JSONB NOT NULL,
  result JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_action_proposal_id ON aion_execution_handoffs(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_trace_id ON aion_execution_handoffs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_actor_id ON aion_execution_handoffs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_workspace_id ON aion_execution_handoffs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_status ON aion_execution_handoffs(status);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_handoff_type ON aion_execution_handoffs(handoff_type);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_target_system ON aion_execution_handoffs(target_system);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_target_request_id ON aion_execution_handoffs(target_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_target_run_id ON aion_execution_handoffs(target_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_execution_handoffs_created_at ON aion_execution_handoffs(created_at);

CREATE TABLE IF NOT EXISTS aion_tool_intent_reviews (
  tool_intent_review_id TEXT PRIMARY KEY,
  tool_intent_id TEXT NOT NULL,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  decision TEXT NOT NULL,
  action_proposal_id TEXT NULL,
  blocker_refs JSONB NOT NULL,
  reason TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_tool_intent_reviews_tool_intent_id ON aion_tool_intent_reviews(tool_intent_id);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intent_reviews_trace_id ON aion_tool_intent_reviews(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intent_reviews_status ON aion_tool_intent_reviews(status);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intent_reviews_decision ON aion_tool_intent_reviews(decision);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intent_reviews_action_proposal_id ON aion_tool_intent_reviews(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intent_reviews_created_at ON aion_tool_intent_reviews(created_at);
