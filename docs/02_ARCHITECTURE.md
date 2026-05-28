# 02 — LPSF Architecture

## v0.1 Architecture

```text
User Query
  ↓
Context Interpreter
  ↓
2nd Brain / Evidence Retrieval
  ↓
Superposed Hypothesis Engine
  ↓
Landscape State Loader
  ↓
Plasticity Mark Resolver
  ↓
Semantic Gravity / Attractor Scorer
  ↓
Collapse Planner
  ↓
LLM Decoder
  ↓
Experience Encoder
  ↓
Plasticity Operator Engine
  ↓
Memory Consolidation / Forgetting
```

## Module Definitions

### 1. Context Interpreter

Extracts:

- user goal;
- domain;
- emotional tone if relevant;
- uncertainty;
- contradiction pressure;
- abstraction level;
- whether the request is theory, implementation, research, or decision.

### 2. Evidence Retrieval

May use:

- BM25 keyword search;
- vector search;
- graph traversal;
- 2nd brain inventory;
- paper/source notes.

Retrieval is not the final memory. It is evidence input.

### 3. Superposed Hypothesis Engine

Creates several candidate interpretations before deciding.

Example:

```text
H1: implementation question
H2: theory question
H3: research planning question
H4: 2nd brain integration question
H5: Codex orchestration question
```

Each hypothesis gets:

```text
amplitude = relevance + landscape_mass + goal_alignment + evidence_support - risk
```

### 4. Landscape State Loader

Loads persistent state:

- attractor depths;
- path weights;
- inhibited paths;
- value field tilts;
- sensitivity profiles;
- schema mappings;
- previous collapse traces;
- plasticity marks.

### 5. Plasticity Mark Resolver

Combines marks by:

- strength;
- half-life;
- context match;
- recency;
- confidence;
- source grounding;
- contradiction status.

### 6. Semantic Gravity / Attractor Scorer

Operational definition of semantic gravity:

```text
semantic gravity = the scoring pressure by which high-mass concepts, goals, memories, values, and unresolved contradictions pull hypotheses and paths toward themselves.
```

Do not leave this as a metaphor. Implement it as a scoring function.

### 7. Collapse Planner

Chooses final response path and records:

- selected hypothesis;
- suppressed hypotheses;
- unresolved contradictions;
- evidence used;
- landscape marks that affected the decision.

### 8. LLM Decoder

Turns the selected path into natural language, code, plans, or structured output.

The LLM is important, but not the whole cognitive architecture.

### 9. Experience Encoder

After response and feedback, encode the experience:

```json
{
  "experience_type": "factual | procedural | evaluative | affective | corrective | research",
  "importance": 0.0,
  "goal_relevance": 0.0,
  "emotional_charge": 0.0,
  "outcome_score": 0.0,
  "suggested_operators": [],
  "targets": []
}
```

### 10. Plasticity Operator Engine

Applies one or more operators from `03_PLASTICITY_OPERATORS.md`.

### 11. Memory Consolidation / Forgetting

Sorts outputs into:

```text
raw_trace
semantic_summary
landscape_mark
forget
```

## v0.1 Implementation Principle

Do not neuralize too early. Start with:

```text
SQLite/Postgres + graph state + JSON traces + LLM decoder
```

Only after the state-change behavior is measured should the project move toward LoRA, activation steering, learned gates, or hypernetworks.

