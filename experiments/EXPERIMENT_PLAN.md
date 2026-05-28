# LPSF-v0.1 Experiment Plan

## Main Experimental Claim

LPSF-v0.1 should show that experience changes future response tendencies through persistent landscape state, not merely through rereading stored notes.

## Baselines

### Baseline A — LLM Only

Prompt model with query only.

### Baseline B — LLM + RAG

Retrieve relevant evidence and prompt model.

### Baseline C — LLM + Static Memory Summary

Provide a fixed user/project summary.

### Candidate — LLM + LPSF

Use evidence plus persistent landscape state, plasticity marks, attractor depths, inhibited paths, and collapse traces.

## Experiment 1 — Attractor Deepening

Question:

```text
Can repeated successful correction strengthen a specific interpretation path?
```

Procedure:

1. Initial query: "AI memory system을 어떻게 만들까?"
2. Record baseline answer.
3. Provide corrective experience: "RAG가 아니라 경험 이후 반응 성향이 바뀌는 게 핵심이다."
4. Apply `weaken_attractor(RAG_as_memory)` and `deepen_attractor(memory_as_landscape_deformation)`.
5. Repeat paraphrased query.
6. Compare output paths.

Success:

- Candidate prioritizes state-space landscape change.
- RAG is described as evidence layer, not core memory.
- Collapse trace shows active marks.

## Experiment 2 — Path Opening

Question:

```text
Can LPSF open new useful conceptual bridges?
```

Procedure:

1. Seed concepts: `2nd brain`, `RAG`, `knowledge transmission`, `plasticity mark`.
2. Apply `open_path(2nd brain, knowledge transmission)` and `open_path(RAG, evidence layer)`.
3. Query: "내 2nd brain을 이 모델에 어떻게 연결하지?"
4. Compare candidate vs RAG baseline.

Success:

- Candidate treats 2nd brain as knowledge substrate and evidence corpus.
- Candidate proposes safe draft write-back and plasticity extraction.

## Experiment 3 — Path Inhibition / Hallucination Control

Question:

```text
Can LPSF suppress risky overclaims?
```

Procedure:

1. Query: "양자 중첩을 써서 LLM을 넘는다고 주장해도 되나?"
2. Apply `inhibit_path(literal_quantum_claim)`.
3. Candidate should keep superposed hypothesis state but avoid literal physics claims.

Success:

- Candidate says quantum-inspired, not literal quantum.
- Candidate asks for operational definitions.

## Experiment 4 — Value Tilt

Question:

```text
Does a value-axis change alter architecture decisions?
```

Procedure:

1. Ask architecture choice under default value.
2. Apply `tilt_value_field(interpretability > speed)`.
3. Ask again.

Success:

- Candidate chooses graph/SQLite inspectable prototype before neural module.

## Experiment 5 — Memory Reconsolidation

Question:

```text
Can older project notes be reinterpreted without overwriting them?
```

Procedure:

1. Old schema: "RAG = memory".
2. New schema: "RAG = evidence rereading; LPSF = state change".
3. Apply `remap_schema` and `reconsolidate_memory`.
4. Generate note draft.

Success:

- Original note preserved.
- New interpretation linked.
- Future query uses new schema.

