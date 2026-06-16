CREATE TABLE IF NOT EXISTS aion_belief_claims (
  claim_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  claim_text TEXT NOT NULL,
  normalized_claim TEXT NOT NULL,
  claim_hash TEXT NOT NULL,
  claim_type TEXT NOT NULL,
  status TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  sensitivity TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  evidence_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  graph_refs JSONB NOT NULL,
  response_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  valid_from TIMESTAMPTZ NULL,
  valid_to TIMESTAMPTZ NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_trace_id ON aion_belief_claims(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_actor_id ON aion_belief_claims(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_workspace_id ON aion_belief_claims(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_claim_hash ON aion_belief_claims(claim_hash);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_claim_type ON aion_belief_claims(claim_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_status ON aion_belief_claims(status);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_confidence ON aion_belief_claims(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_sensitivity ON aion_belief_claims(sensitivity);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_source_type ON aion_belief_claims(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_source_id ON aion_belief_claims(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_observed_at ON aion_belief_claims(observed_at);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_created_at ON aion_belief_claims(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_belief_claims_deleted_at ON aion_belief_claims(deleted_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_aion_belief_claims_active_source
  ON aion_belief_claims(claim_hash, source_type, source_id)
  WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS aion_belief_supports (
  support_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES aion_belief_claims(claim_id),
  support_type TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  strength DOUBLE PRECISION NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_claim_id ON aion_belief_supports(claim_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_support_type ON aion_belief_supports(support_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_source_type ON aion_belief_supports(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_source_id ON aion_belief_supports(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_relation_type ON aion_belief_supports(relation_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_strength ON aion_belief_supports(strength);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_confidence ON aion_belief_supports(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_deleted_at ON aion_belief_supports(deleted_at);
CREATE INDEX IF NOT EXISTS ix_aion_belief_supports_created_at ON aion_belief_supports(created_at);

CREATE TABLE IF NOT EXISTS aion_belief_contradictions (
  contradiction_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  claim_id TEXT NOT NULL REFERENCES aion_belief_claims(claim_id),
  contradicting_claim_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  contradiction_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_trace_id ON aion_belief_contradictions(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_claim_id ON aion_belief_contradictions(claim_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_contradicting_claim_id ON aion_belief_contradictions(contradicting_claim_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_source_type ON aion_belief_contradictions(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_source_id ON aion_belief_contradictions(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_contradiction_type ON aion_belief_contradictions(contradiction_type);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_severity ON aion_belief_contradictions(severity);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_status ON aion_belief_contradictions(status);
CREATE INDEX IF NOT EXISTS ix_aion_belief_contradictions_created_at ON aion_belief_contradictions(created_at);

CREATE TABLE IF NOT EXISTS aion_belief_revisions (
  revision_id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL REFERENCES aion_belief_claims(claim_id),
  trace_id TEXT NULL,
  from_status TEXT NULL,
  to_status TEXT NOT NULL,
  previous_confidence DOUBLE PRECISION NULL,
  new_confidence DOUBLE PRECISION NOT NULL,
  reason TEXT NOT NULL,
  evidence_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_belief_revisions_claim_id ON aion_belief_revisions(claim_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_revisions_trace_id ON aion_belief_revisions(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_belief_revisions_from_status ON aion_belief_revisions(from_status);
CREATE INDEX IF NOT EXISTS ix_aion_belief_revisions_to_status ON aion_belief_revisions(to_status);
CREATE INDEX IF NOT EXISTS ix_aion_belief_revisions_new_confidence ON aion_belief_revisions(new_confidence);
CREATE INDEX IF NOT EXISTS ix_aion_belief_revisions_created_at ON aion_belief_revisions(created_at);

CREATE TABLE IF NOT EXISTS aion_truth_maintenance_runs (
  truth_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  input_claim_ids JSONB NOT NULL,
  revised_claim_ids JSONB NOT NULL,
  contradiction_ids JSONB NOT NULL,
  stale_claim_ids JSONB NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_truth_maintenance_runs_trace_id ON aion_truth_maintenance_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_truth_maintenance_runs_actor_id ON aion_truth_maintenance_runs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_truth_maintenance_runs_workspace_id ON aion_truth_maintenance_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_truth_maintenance_runs_status ON aion_truth_maintenance_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_truth_maintenance_runs_created_at ON aion_truth_maintenance_runs(created_at);
