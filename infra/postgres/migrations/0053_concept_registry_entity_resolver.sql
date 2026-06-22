CREATE TABLE IF NOT EXISTS aion_concepts (
    concept_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    concept_type TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    aliases JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_concepts_normalized_name ON aion_concepts (normalized_name);
CREATE INDEX IF NOT EXISTS ix_aion_concepts_concept_type ON aion_concepts (concept_type);
CREATE INDEX IF NOT EXISTS ix_aion_concepts_status ON aion_concepts (status);
CREATE INDEX IF NOT EXISTS ix_aion_concepts_created_at ON aion_concepts (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_concepts_archived_at ON aion_concepts (archived_at);

CREATE TABLE IF NOT EXISTS aion_entities (
    entity_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    canonical_name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    concept_refs JSONB NOT NULL,
    evidence_refs JSONB NOT NULL,
    memory_refs JSONB NOT NULL,
    belief_refs JSONB NOT NULL,
    graph_refs JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    sensitivity TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NULL DEFAULT now(),
    merged_into_entity_id TEXT NULL,
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_entities_normalized_name ON aion_entities (normalized_name);
CREATE INDEX IF NOT EXISTS ix_aion_entities_entity_type ON aion_entities (entity_type);
CREATE INDEX IF NOT EXISTS ix_aion_entities_status ON aion_entities (status);
CREATE INDEX IF NOT EXISTS ix_aion_entities_confidence ON aion_entities (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_entities_created_at ON aion_entities (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_entities_deleted_at ON aion_entities (deleted_at);

CREATE TABLE IF NOT EXISTS aion_entity_aliases (
    alias_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    alias TEXT NOT NULL,
    normalized_alias TEXT NOT NULL,
    alias_type TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    source_type TEXT NULL,
    source_id TEXT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_entity_aliases_entity_id ON aion_entity_aliases (entity_id);
CREATE INDEX IF NOT EXISTS ix_aion_entity_aliases_normalized_alias ON aion_entity_aliases (normalized_alias);
CREATE INDEX IF NOT EXISTS ix_aion_entity_aliases_alias_type ON aion_entity_aliases (alias_type);
CREATE INDEX IF NOT EXISTS ix_aion_entity_aliases_deleted_at ON aion_entity_aliases (deleted_at);

CREATE TABLE IF NOT EXISTS aion_entity_mentions (
    mention_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    entity_id TEXT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    mention_text TEXT NOT NULL,
    normalized_mention TEXT NOT NULL,
    mention_type TEXT NOT NULL,
    start_char INTEGER NULL,
    end_char INTEGER NULL,
    confidence DOUBLE PRECISION NOT NULL,
    resolved BOOLEAN NOT NULL,
    resolution_score DOUBLE PRECISION NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_entity_mentions_entity_id ON aion_entity_mentions (entity_id);
CREATE INDEX IF NOT EXISTS ix_aion_entity_mentions_trace_id ON aion_entity_mentions (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_entity_mentions_source ON aion_entity_mentions (source_type, source_id);
CREATE INDEX IF NOT EXISTS ix_aion_entity_mentions_normalized_mention ON aion_entity_mentions (normalized_mention);
CREATE INDEX IF NOT EXISTS ix_aion_entity_mentions_resolved ON aion_entity_mentions (resolved);
CREATE INDEX IF NOT EXISTS ix_aion_entity_mentions_deleted_at ON aion_entity_mentions (deleted_at);

CREATE TABLE IF NOT EXISTS aion_reference_links (
    reference_link_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    entity_id TEXT NULL,
    concept_id TEXT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    evidence_refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_reference_links_trace_id ON aion_reference_links (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_reference_links_source ON aion_reference_links (source_type, source_id);
CREATE INDEX IF NOT EXISTS ix_aion_reference_links_target ON aion_reference_links (target_type, target_id);
CREATE INDEX IF NOT EXISTS ix_aion_reference_links_entity_id ON aion_reference_links (entity_id);
CREATE INDEX IF NOT EXISTS ix_aion_reference_links_concept_id ON aion_reference_links (concept_id);
CREATE INDEX IF NOT EXISTS ix_aion_reference_links_relation_type ON aion_reference_links (relation_type);
CREATE INDEX IF NOT EXISTS ix_aion_reference_links_deleted_at ON aion_reference_links (deleted_at);

CREATE TABLE IF NOT EXISTS aion_entity_resolution_runs (
    resolution_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    source_type TEXT NULL,
    source_id TEXT NULL,
    result JSONB NOT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_entity_resolution_runs_trace_id ON aion_entity_resolution_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_entity_resolution_runs_status ON aion_entity_resolution_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_entity_resolution_runs_source ON aion_entity_resolution_runs (source_type, source_id);

CREATE TABLE IF NOT EXISTS aion_entity_merge_proposals (
    merge_proposal_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    primary_entity_id TEXT NOT NULL,
    duplicate_entity_id TEXT NOT NULL,
    status TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    reason TEXT NOT NULL,
    evidence_refs JSONB NOT NULL,
    approval_request_id TEXT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_entity_merge_proposals_status ON aion_entity_merge_proposals (status);
CREATE INDEX IF NOT EXISTS ix_aion_entity_merge_proposals_primary ON aion_entity_merge_proposals (primary_entity_id);
CREATE INDEX IF NOT EXISTS ix_aion_entity_merge_proposals_duplicate ON aion_entity_merge_proposals (duplicate_entity_id);

CREATE TABLE IF NOT EXISTS aion_entity_split_proposals (
    split_proposal_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    entity_id TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    proposed_entities JSONB NOT NULL,
    evidence_refs JSONB NOT NULL,
    approval_request_id TEXT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_entity_split_proposals_status ON aion_entity_split_proposals (status);
CREATE INDEX IF NOT EXISTS ix_aion_entity_split_proposals_entity_id ON aion_entity_split_proposals (entity_id);
