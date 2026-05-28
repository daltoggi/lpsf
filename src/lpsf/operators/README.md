# LPSF M3 Operators

This package implements the eight v0.1 plasticity operators from
`docs/lpsf/LPSF_SPEC.md` section 5. Operators are pure state functions over a
provided SQLite connection: they validate an existing `experience_event` and
`evidence_snapshot`, validate evidence reference ids, write a `plasticity_mark`,
update the relevant secondary landscape table, and return:

```python
{"mark_id": "...", "state_delta": {...}, "warnings": [...]}
```

They do not call LLMs, retrieval indexes, network services, or local personal
knowledge-base paths.

## Contracts

- `STRENGTH_CAP` is `1.0`, matching the M2 schema check range and preventing
  unbounded score growth.
- `half_life` is an integer number of seconds. `None` would mean permanent, and
  permanent marks are blocked in v0.1 until a review policy exists.
- `evidence_refs` must be non-empty string ids. Bodies, dicts, empty refs, and
  suspiciously long refs are rejected.
- Priority warnings follow `priority.ORDER`: inhibition is highest; sensitivity
  modulation is lowest.
- Reversal and latest semantics are stored in `plasticity_marks` through active
  mark supersession. M2 secondary tables do not all have status columns, so M3
  does not extend the schema.

## Decay

`apply_decay(conn, now, snapshot_id)` is deterministic over the supplied
timestamp. For tables whose M2 unique constraints prevent inserting another row
with the exact same logical key, decayed rows use versioned keys while recording
the original key in `decay_state`.

## Extending In M4+

Future experiment runners should call these functions after encoding a
synthetic or approved event. M4 may build collapse scoring and baseline
comparisons on top of the returned `mark_id` and secondary state deltas, but
operators should remain isolated from LLM, RAG, and network calls.
