# 09 — LPSF-v0.1 Spec

## Objective

Create a minimal inspectable prototype proving that experience can modify future response tendencies through persistent landscape state.

## Core Data Structures

```text
ExperienceEvent
ConceptNode
SemanticEdge
Attractor
PlasticityMark
HypothesisState
InterferenceMatrix
CollapseTrace
EvaluationRun
SecondBrainSource
```

## Core Functions

```python
encode_experience(event_text, context) -> ExperienceEvent
retrieve_evidence(query, second_brain_index) -> EvidenceSet
generate_hypotheses(query, context, evidence) -> list[HypothesisState]
load_landscape_state(context) -> LandscapeState
score_hypotheses(hypotheses, landscape_state) -> ScoreBreakdown
collapse(hypotheses, scores) -> CollapseTrace
compose_answer(collapse_trace, evidence) -> str
apply_plasticity(experience_event, collapse_trace, feedback) -> list[PlasticityMark]
consolidate_memory(experience_event, marks) -> MemoryDecision
```

## Minimum Synthetic Data

Seed concepts:

```text
memory
RAG
state-space landscape
experience
attractor
plasticity mark
2nd brain
semantic field
hypothesis
collapse
forgetting
```

Seed paths:

```text
RAG -> evidence retrieval
memory -> landscape deformation
experience -> plasticity mark
2nd brain -> knowledge substrate
source grounding -> hallucination control
```

Seed inhibited paths:

```text
RAG = true memory
literal quantum physics claim
raw private notes -> public output
```

## Minimal Demo Flow

1. Ask: `AI memory를 어떻게 만들까?`
2. Baseline answers with RAG/static memory.
3. Corrective experience: `RAG가 아니라 경험 이후 반응 성향이 변해야 한다.`
4. Apply:
   - weaken_attractor: `RAG_as_memory`
   - deepen_attractor: `memory_as_landscape_deformation`
   - remap_schema: `memory = stored text` → `memory = landscape deformation`
5. Ask paraphrase: `내 2nd brain을 AI 기억으로 쓰려면?`
6. Candidate should answer with 2nd brain as evidence + landscape marks + safe writeback.
7. Collapse trace should cite active marks.

## Success Criteria

- Candidate output changes for the right reason.
- Change is traceable.
- Baseline does not show same structured shift.
- No raw private 2nd brain content is leaked.
- The implementation can export state.

