# 03 — Plasticity Operators

These are the core update operations for LPSF.

Each operator must be explicit, inspectable, reversible or decayable when possible, and tied to an experience event.

## Common Operator Schema

```json
{
  "operator_type": "string",
  "target_type": "node | edge | path | value_axis | sensitivity_profile | schema | memory",
  "target_id": "string",
  "strength": 0.0,
  "half_life": "short | session | episodic | long | permanent_review_required",
  "source_experience_id": "string",
  "reason": "string",
  "evidence_refs": [],
  "created_at": "timestamp",
  "status": "active | decayed | reversed | superseded"
}
```

## 1. deepen_attractor

Purpose:

Strengthen a useful response path so it activates more easily later.

Example:

```text
Repeatedly successful interpretation:
"RAG is evidence retrieval, not true memory"
```

Effect:

- Increase semantic mass of target path.
- Lower activation threshold.
- Increase ranking score when matching context appears.

Pseudo:

```python
def deepen_attractor(path_id, strength, half_life, reason):
    attractor.depth += strength
    attractor.activation_threshold -= strength * 0.1
    store_mark("deepen_attractor", path_id, strength, half_life, reason)
```

## 2. weaken_attractor

Purpose:

Weaken an automatic but unhelpful response path.

Example:

```text
User corrects: "This is not just RAG. It is experience-induced state change."
```

Effect:

- Decrease path priority.
- Add warning tag if path is selected too early.
- Require more evidence for activation.

## 3. open_path

Purpose:

Create or strengthen a connection between concepts that were previously distant.

Examples:

```text
state-space plasticity ↔ attractor dynamics
second brain ↔ knowledge transmission
epigenetics ↔ expression gating
emotion ↔ gain/precision modulation
```

Effect:

- Add edge.
- Increase graph proximity.
- Enable retrieval bridge.
- Add relation type and evidence.

## 4. inhibit_path

Purpose:

Suppress risky, hallucination-prone, or forbidden paths.

Examples:

```text
literal quantum brain claim
unverified biological epigenetic equivalence
raw private notes → public commit
```

Effect:

- Decrease path weight.
- Increase hallucination penalty.
- Require explicit confirmation if selected.

## 5. tilt_value_field

Purpose:

Change priority axes used during judgment.

Examples:

```text
interpretability > speed
source-grounding > novelty
state-change proof > impressive prose
```

Effect:

- Adjust scoring weights.
- Influence plan selection and architecture choices.

## 6. modulate_sensitivity

Purpose:

Change activation gain/threshold for a trigger pattern.

Examples:

```text
When user says "LLM을 넘고 싶어", increase architecture/research ambition mode.
When user says "환각주의", increase source-grounding threshold.
```

Effect:

- Increase/decrease trigger gain.
- Modify context interpreter weights.

## 7. remap_schema

Purpose:

Replace an old conceptual schema with a better one.

Example:

```text
Old: memory = stored text
New: memory = response-tendency landscape change
```

Effect:

- Update schema mapping.
- Reinterpret older notes.
- Mark old schema as partially deprecated.

## 8. reconsolidate_memory

Purpose:

Change the meaning of an old memory under a new schema.

Example:

```text
Old note: "RAG as memory"
Reconsolidated: "RAG as evidence rereading; LPSF as state change"
```

Effect:

- Preserve original note.
- Add reinterpretation note.
- Link source, old schema, new schema, and reason.

## Operator Priority

When several operators apply:

```text
safety inhibition > source grounding > schema remapping > path opening > attractor deepening > value tilt > sensitivity modulation
```

## Required Tests

Each operator should have deterministic tests:

1. Applying the operator changes state as expected.
2. Decay reduces effect over time.
3. Source experience is traceable.
4. Unsafe operator application is blocked.
5. Repeated application does not create unbounded scores without cap.

