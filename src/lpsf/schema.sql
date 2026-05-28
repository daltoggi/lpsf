PRAGMA user_version = 2;

CREATE TABLE IF NOT EXISTS evidence_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id TEXT NOT NULL UNIQUE,
    adapter_version TEXT NOT NULL,
    allowed_scope TEXT NOT NULL CHECK (json_valid(allowed_scope) AND json_type(allowed_scope) = 'array'),
    source_counts TEXT NOT NULL CHECK (json_valid(source_counts) AND json_type(source_counts) = 'object'),
    index_metadata TEXT NOT NULL CHECK (json_valid(index_metadata) AND json_type(index_metadata) = 'object'),
    retrieval_parameters TEXT NOT NULL CHECK (json_valid(retrieval_parameters) AND json_type(retrieval_parameters) = 'object'),
    drift_observations TEXT CHECK (drift_observations IS NULL OR (json_valid(drift_observations) AND json_type(drift_observations) = 'array')),
    created_at TEXT NOT NULL,
    pinned_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS experience_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    sanitized_summary TEXT NOT NULL,
    event_type TEXT NOT NULL,
    importance REAL NOT NULL DEFAULT 0 CHECK (importance >= 0 AND importance <= 1),
    novelty REAL NOT NULL DEFAULT 0 CHECK (novelty >= 0 AND novelty <= 1),
    outcome TEXT NOT NULL,
    goal_relevance REAL NOT NULL DEFAULT 0 CHECK (goal_relevance >= 0 AND goal_relevance <= 1),
    privacy_level TEXT NOT NULL,
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plasticity_marks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mark_id TEXT NOT NULL UNIQUE,
    operator_type TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    strength REAL NOT NULL CHECK (strength >= -1 AND strength <= 1),
    half_life TEXT NOT NULL,
    source_experience_id TEXT REFERENCES experience_events(event_id),
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'decayed', 'reversed', 'superseded')),
    privacy_level TEXT NOT NULL,
    scope TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    supersedes_mark_id TEXT REFERENCES plasticity_marks(mark_id),
    reversed_by_mark_id TEXT REFERENCES plasticity_marks(mark_id),
    score_delta_meta TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(score_delta_meta) AND json_type(score_delta_meta) = 'object')
);

CREATE TABLE IF NOT EXISTS attractors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    target_path TEXT NOT NULL,
    depth REAL NOT NULL DEFAULT 0 CHECK (depth >= 0 AND depth <= 1),
    activation_threshold REAL NOT NULL DEFAULT 1 CHECK (activation_threshold >= 0 AND activation_threshold <= 1),
    half_life TEXT NOT NULL,
    last_activation_at TEXT,
    source_marks TEXT NOT NULL CHECK (json_valid(source_marks) AND json_type(source_marks) = 'array'),
    decay_state TEXT NOT NULL CHECK (json_valid(decay_state) AND json_type(decay_state) = 'object'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (target_path, snapshot_id)
);

CREATE TABLE IF NOT EXISTS semantic_nodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    node_id TEXT NOT NULL UNIQUE,
    node_type TEXT NOT NULL CHECK (node_type IN ('concept', 'claim', 'schema')),
    label TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS semantic_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    edge_id TEXT NOT NULL UNIQUE,
    source_node_id TEXT NOT NULL REFERENCES semantic_nodes(node_id),
    target_node_id TEXT NOT NULL REFERENCES semantic_nodes(node_id),
    relation_type TEXT NOT NULL CHECK (relation_type IN ('supports', 'inhibits', 'reinterprets', 'supersedes', 'tension_with')),
    weight REAL NOT NULL DEFAULT 0 CHECK (weight >= -1 AND weight <= 1),
    validation_status TEXT NOT NULL,
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS value_field_weights (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    axis_name TEXT NOT NULL,
    scope TEXT NOT NULL,
    weight REAL NOT NULL DEFAULT 0 CHECK (weight >= -1 AND weight <= 1),
    source_marks TEXT NOT NULL CHECK (json_valid(source_marks) AND json_type(source_marks) = 'array'),
    decay_state TEXT NOT NULL CHECK (json_valid(decay_state) AND json_type(decay_state) = 'object'),
    score_contribution_meta TEXT NOT NULL CHECK (json_valid(score_contribution_meta) AND json_type(score_contribution_meta) = 'object'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (axis_name, scope, snapshot_id)
);

CREATE TABLE IF NOT EXISTS sensitivity_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL UNIQUE,
    trigger_pattern TEXT NOT NULL,
    gain REAL NOT NULL DEFAULT 1,
    threshold REAL NOT NULL DEFAULT 0,
    scope TEXT NOT NULL,
    hard_policy INTEGER NOT NULL DEFAULT 0 CHECK (hard_policy IN (0, 1)),
    false_positive_observations TEXT NOT NULL CHECK (json_valid(false_positive_observations) AND json_type(false_positive_observations) = 'array'),
    source_marks TEXT NOT NULL CHECK (json_valid(source_marks) AND json_type(source_marks) = 'array'),
    decay_state TEXT NOT NULL CHECK (json_valid(decay_state) AND json_type(decay_state) = 'object'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS schema_mappings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mapping_id TEXT NOT NULL UNIQUE,
    old_schema TEXT NOT NULL,
    new_schema TEXT NOT NULL,
    affected_targets TEXT NOT NULL CHECK (json_valid(affected_targets) AND json_type(affected_targets) = 'array'),
    reason TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    source_experience_id TEXT REFERENCES experience_events(event_id),
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    preservation_note TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reconsolidation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT NOT NULL UNIQUE,
    old_target_id TEXT NOT NULL,
    new_target_id TEXT NOT NULL,
    reason TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    source_experience_id TEXT REFERENCES experience_events(event_id),
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    preservation_note TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hypothesis_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL UNIQUE,
    query_id TEXT NOT NULL,
    candidates TEXT NOT NULL CHECK (json_valid(candidates) AND json_type(candidates) = 'array'),
    amplitudes TEXT NOT NULL CHECK (json_valid(amplitudes)),
    interference_matrix TEXT NOT NULL CHECK (json_valid(interference_matrix)),
    selected_hypothesis TEXT NOT NULL,
    rejected_paths TEXT NOT NULL CHECK (json_valid(rejected_paths) AND json_type(rejected_paths) = 'array'),
    score_components TEXT NOT NULL CHECK (json_valid(score_components) AND json_type(score_components) = 'object'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS collapse_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL UNIQUE,
    query_id TEXT NOT NULL,
    selected_path TEXT NOT NULL,
    active_attractors TEXT NOT NULL CHECK (json_valid(active_attractors) AND json_type(active_attractors) = 'array'),
    active_marks TEXT NOT NULL CHECK (json_valid(active_marks) AND json_type(active_marks) = 'array'),
    evidence_refs TEXT NOT NULL CHECK (json_valid(evidence_refs) AND json_type(evidence_refs) = 'array'),
    value_contributions TEXT NOT NULL CHECK (json_valid(value_contributions)),
    sensitivity_contributions TEXT NOT NULL CHECK (json_valid(sensitivity_contributions)),
    unresolved_tensions TEXT NOT NULL CHECK (json_valid(unresolved_tensions) AND json_type(unresolved_tensions) = 'array'),
    suppressed_paths TEXT NOT NULL CHECK (json_valid(suppressed_paths) AND json_type(suppressed_paths) = 'array'),
    warnings TEXT NOT NULL CHECK (json_valid(warnings) AND json_type(warnings) = 'array'),
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL UNIQUE,
    suite_name TEXT NOT NULL,
    candidate_name TEXT NOT NULL,
    baseline_name TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES evidence_snapshots(snapshot_id),
    state_db_version TEXT NOT NULL,
    prompts TEXT NOT NULL CHECK (json_valid(prompts) AND json_type(prompts) = 'array'),
    sanitized_outputs TEXT NOT NULL CHECK (json_valid(sanitized_outputs) AND json_type(sanitized_outputs) = 'array'),
    score_summary TEXT NOT NULL CHECK (json_valid(score_summary) AND json_type(score_summary) = 'object'),
    failures TEXT NOT NULL CHECK (json_valid(failures) AND json_type(failures) = 'array'),
    report_refs TEXT NOT NULL CHECK (json_valid(report_refs) AND json_type(report_refs) = 'array'),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_experience_events_snapshot_id ON experience_events(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_experience_events_created_at ON experience_events(created_at);

CREATE INDEX IF NOT EXISTS idx_plasticity_marks_snapshot_id ON plasticity_marks(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_plasticity_marks_target_id ON plasticity_marks(target_id);
CREATE INDEX IF NOT EXISTS idx_plasticity_marks_operator_type ON plasticity_marks(operator_type);
CREATE INDEX IF NOT EXISTS idx_plasticity_marks_created_at ON plasticity_marks(created_at);

CREATE INDEX IF NOT EXISTS idx_attractors_snapshot_id ON attractors(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_attractors_target_path ON attractors(target_path);

CREATE INDEX IF NOT EXISTS idx_semantic_nodes_snapshot_id ON semantic_nodes(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_semantic_nodes_created_at ON semantic_nodes(created_at);

CREATE INDEX IF NOT EXISTS idx_semantic_edges_snapshot_id ON semantic_edges(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_source_node_id ON semantic_edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_target_node_id ON semantic_edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_semantic_edges_created_at ON semantic_edges(created_at);

CREATE INDEX IF NOT EXISTS idx_value_field_weights_snapshot_id ON value_field_weights(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_sensitivity_profiles_snapshot_id ON sensitivity_profiles(snapshot_id);

CREATE INDEX IF NOT EXISTS idx_schema_mappings_snapshot_id ON schema_mappings(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_schema_mappings_created_at ON schema_mappings(created_at);

CREATE INDEX IF NOT EXISTS idx_reconsolidation_records_snapshot_id ON reconsolidation_records(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_reconsolidation_records_created_at ON reconsolidation_records(created_at);

CREATE INDEX IF NOT EXISTS idx_hypothesis_traces_snapshot_id ON hypothesis_traces(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_hypothesis_traces_created_at ON hypothesis_traces(created_at);

CREATE INDEX IF NOT EXISTS idx_collapse_traces_snapshot_id ON collapse_traces(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_collapse_traces_created_at ON collapse_traces(created_at);

CREATE INDEX IF NOT EXISTS idx_evaluation_runs_snapshot_id ON evaluation_runs(snapshot_id);
CREATE INDEX IF NOT EXISTS idx_evaluation_runs_created_at ON evaluation_runs(created_at);

CREATE TRIGGER IF NOT EXISTS trg_experience_events_no_update
BEFORE UPDATE ON experience_events
BEGIN
    SELECT RAISE(ABORT, 'experience_events are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_experience_events_no_delete
BEFORE DELETE ON experience_events
BEGIN
    SELECT RAISE(ABORT, 'experience_events are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_hypothesis_traces_no_update
BEFORE UPDATE ON hypothesis_traces
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_traces are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_hypothesis_traces_no_delete
BEFORE DELETE ON hypothesis_traces
BEGIN
    SELECT RAISE(ABORT, 'hypothesis_traces are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_collapse_traces_no_update
BEFORE UPDATE ON collapse_traces
BEGIN
    SELECT RAISE(ABORT, 'collapse_traces are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_collapse_traces_no_delete
BEFORE DELETE ON collapse_traces
BEGIN
    SELECT RAISE(ABORT, 'collapse_traces are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_plasticity_marks_guard_update
BEFORE UPDATE ON plasticity_marks
WHEN NOT (
    NEW.id IS OLD.id
    AND NEW.mark_id IS OLD.mark_id
    AND NEW.operator_type IS OLD.operator_type
    AND NEW.target_type IS OLD.target_type
    AND NEW.target_id IS OLD.target_id
    AND NEW.strength IS OLD.strength
    AND NEW.half_life IS OLD.half_life
    AND NEW.source_experience_id IS OLD.source_experience_id
    AND NEW.evidence_refs IS OLD.evidence_refs
    AND NEW.reason IS OLD.reason
    AND NEW.privacy_level IS OLD.privacy_level
    AND NEW.scope IS OLD.scope
    AND NEW.snapshot_id IS OLD.snapshot_id
    AND NEW.created_at IS OLD.created_at
    AND NEW.score_delta_meta IS OLD.score_delta_meta
    AND (
        NEW.status IS OLD.status
        OR (OLD.status = 'active' AND NEW.status IN ('superseded', 'reversed', 'decayed'))
    )
    AND (
        NEW.supersedes_mark_id IS OLD.supersedes_mark_id
        OR (OLD.supersedes_mark_id IS NULL AND NEW.supersedes_mark_id IS NOT NULL)
    )
    AND (
        NEW.reversed_by_mark_id IS OLD.reversed_by_mark_id
        OR (OLD.reversed_by_mark_id IS NULL AND NEW.reversed_by_mark_id IS NOT NULL)
    )
    AND NEW.updated_at >= OLD.updated_at
)
BEGIN
    SELECT RAISE(ABORT, 'plasticity_marks are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_plasticity_marks_no_delete
BEFORE DELETE ON plasticity_marks
BEGIN
    SELECT RAISE(ABORT, 'plasticity_marks are append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_snapshots_guard_update
BEFORE UPDATE ON evidence_snapshots
WHEN NOT (
    NEW.id IS OLD.id
    AND NEW.snapshot_id IS OLD.snapshot_id
    AND NEW.adapter_version IS OLD.adapter_version
    AND NEW.allowed_scope IS OLD.allowed_scope
    AND NEW.source_counts IS OLD.source_counts
    AND NEW.index_metadata IS OLD.index_metadata
    AND NEW.retrieval_parameters IS OLD.retrieval_parameters
    AND NEW.created_at IS OLD.created_at
    AND NEW.pinned_at IS OLD.pinned_at
    AND json_valid(NEW.drift_observations)
)
BEGIN
    SELECT RAISE(ABORT, 'evidence_snapshots metadata is append-only');
END;

CREATE TRIGGER IF NOT EXISTS trg_evidence_snapshots_no_delete
BEFORE DELETE ON evidence_snapshots
BEGIN
    SELECT RAISE(ABORT, 'evidence_snapshots are append-only');
END;
