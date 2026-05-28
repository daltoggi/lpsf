# 05 — DB Schema Draft

This is a schema target for SQLite/Postgres. v0.1 can start with SQLite.

## experience_events

```sql
CREATE TABLE experience_events (
  id TEXT PRIMARY KEY,
  raw_text TEXT,
  summary TEXT,
  experience_type TEXT NOT NULL,
  importance_score REAL DEFAULT 0,
  novelty_score REAL DEFAULT 0,
  emotional_charge REAL DEFAULT 0,
  goal_relevance REAL DEFAULT 0,
  outcome_score REAL DEFAULT 0,
  privacy_level TEXT DEFAULT 'private',
  source_ref TEXT,
  created_at TEXT NOT NULL
);
```

## concept_nodes

```sql
CREATE TABLE concept_nodes (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  type TEXT NOT NULL,
  summary TEXT,
  semantic_mass REAL DEFAULT 0,
  value_relevance REAL DEFAULT 0,
  sensitivity_gain REAL DEFAULT 1,
  abstraction_level REAL DEFAULT 0,
  source_refs TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## semantic_edges

```sql
CREATE TABLE semantic_edges (
  id TEXT PRIMARY KEY,
  source_node_id TEXT NOT NULL,
  target_node_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  base_weight REAL DEFAULT 0,
  current_weight REAL DEFAULT 0,
  contradiction_score REAL DEFAULT 0,
  evidence_refs TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## attractors

```sql
CREATE TABLE attractors (
  id TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  target_path TEXT NOT NULL,
  depth REAL DEFAULT 0,
  activation_threshold REAL DEFAULT 1,
  half_life TEXT DEFAULT 'episodic',
  last_activated TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## plasticity_marks

```sql
CREATE TABLE plasticity_marks (
  id TEXT PRIMARY KEY,
  operator_type TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_id TEXT NOT NULL,
  strength REAL NOT NULL,
  half_life TEXT NOT NULL,
  source_experience_id TEXT,
  reason TEXT,
  evidence_refs TEXT,
  status TEXT DEFAULT 'active',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

## hypothesis_traces

```sql
CREATE TABLE hypothesis_traces (
  id TEXT PRIMARY KEY,
  query TEXT NOT NULL,
  hypotheses_json TEXT NOT NULL,
  amplitudes_json TEXT NOT NULL,
  interference_matrix_json TEXT,
  selected_hypothesis TEXT,
  selected_path TEXT,
  rejected_paths_json TEXT,
  final_answer TEXT,
  created_at TEXT NOT NULL
);
```

## collapse_traces

```sql
CREATE TABLE collapse_traces (
  id TEXT PRIMARY KEY,
  hypothesis_trace_id TEXT,
  active_attractors_json TEXT,
  active_marks_json TEXT,
  evidence_refs TEXT,
  score_breakdown_json TEXT,
  unresolved_contradictions_json TEXT,
  hallucination_warnings_json TEXT,
  created_at TEXT NOT NULL
);
```

## second_brain_sources

```sql
CREATE TABLE second_brain_sources (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  title TEXT,
  tags TEXT,
  summary TEXT,
  sensitivity_level TEXT DEFAULT 'unknown',
  last_seen_at TEXT NOT NULL,
  hash TEXT,
  indexed_status TEXT DEFAULT 'pending'
);
```

## evaluation_runs

```sql
CREATE TABLE evaluation_runs (
  id TEXT PRIMARY KEY,
  suite_name TEXT NOT NULL,
  baseline_name TEXT NOT NULL,
  candidate_name TEXT NOT NULL,
  score_json TEXT,
  report_path TEXT,
  created_at TEXT NOT NULL
);
```

## Notes

- Store raw private notes outside the experiment DB if possible.
- Use hashes for source tracking when privacy risk is high.
- Use append-only logs for plasticity marks.
- Never silently mutate old traces.

