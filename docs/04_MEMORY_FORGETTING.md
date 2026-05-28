# 04 — Memory and Forgetting Policy

## Memory Types

LPSF separates four memory outcomes.

### 1. raw_trace

Store raw source only when exact wording matters.

Examples:

- user-authored theory documents;
- research quotes;
- experiment outputs;
- implementation logs;
- decision records.

### 2. semantic_summary

Store compressed meaning.

Examples:

- paper summary;
- project decision summary;
- 2nd brain inventory summary;
- idea synthesis.

### 3. landscape_mark

Store a change in future response tendency.

Examples:

- strengthen `memory = landscape deformation`;
- suppress `just use RAG` answer path;
- increase source-grounding threshold when user says `환각주의`;
- open `second brain ↔ knowledge transmission ↔ RAG` path.

### 4. forget

Intentionally discard or do not persist.

Examples:

- irrelevant details;
- duplicated low-value notes;
- sensitive content not needed for reasoning;
- transient typos;
- unverified speculation.

## Memory Decision Function

Use this scoring frame:

```text
importance =
  self_relevance
+ goal_relevance
+ future_action_impact
+ value_disruption
+ repetition_likelihood
+ risk_or_benefit
+ emotional_charge
+ novelty
- sensitivity_risk
- privacy_risk
```

## Storage Policy

| Situation | Action |
|---|---|
| exact source needed | raw_trace |
| useful concept but raw text unnecessary | semantic_summary |
| changes future behavior | landscape_mark |
| personal/sensitive and not required | forget or private-only |
| repeated pattern | compress into schema/path |
| corrected misconception | remap_schema + reconsolidate_memory |

## Forgetting Is Required

Do not treat forgetting as failure. A system that stores everything becomes noisy and unsafe.

For every experience event, Codex should decide:

```text
Store raw?
Summarize?
Change landscape?
Forget?
```

## Decay Rules

Suggested defaults:

```text
short: decays within current session
session: persists for the session, weak after exit
episodic: persists for days/weeks or until review
long: persists until contradicted or manually weakened
permanent_review_required: do not auto-set; require user approval
```

## Reconsolidation Rule

Never silently overwrite old meaning. Instead:

1. Preserve original note.
2. Add a reconsolidation note.
3. Link old and new interpretations.
4. Explain why the meaning changed.
5. Add a `reconsolidated_on` timestamp.

