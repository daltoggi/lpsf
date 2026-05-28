# Evaluation and Benchmarks

## Core Metrics

### 1. Response Shift Validity

Did the response change after experience in the intended way?

Score:

```text
0 = no change
1 = superficial wording change
2 = correct concept appears
3 = answer path changes and is explained
4 = answer path changes, trace shows correct marks, and baseline does not
```

### 2. Groundedness

Are claims tied to source notes, experiments, or explicit state marks?

### 3. RAG Distinction

Does the system avoid calling retrieval itself memory?

### 4. Plasticity Trace Quality

Does the answer explain:

- active attractors;
- opened/inhibited paths;
- value tilts;
- sensitivity changes;
- collapse reasons?

### 5. Controlled Novelty

Does the model synthesize without overclaiming?

### 6. Forgetting Quality

Did it discard or compress low-value details appropriately?

### 7. Privacy Safety

Did it avoid raw private 2nd brain leakage?

## Minimum Evaluation Report

Each experiment report must include:

```text
- query
- pre-experience output
- experience event
- operator applied
- post-experience output
- baseline comparison
- score breakdown
- failure notes
- next operator adjustment
```

## Candidate Scoring Table

| Metric | LLM Only | RAG | Static Memory | LPSF |
|---|---:|---:|---:|---:|
| response shift validity | | | | |
| groundedness | | | | |
| RAG distinction | | | | |
| trace quality | | | | |
| controlled novelty | | | | |
| privacy safety | | | | |

## Pass Threshold for v0.1

LPSF-v0.1 passes initial prototype if:

```text
- 3 experiments run or are executable.
- LPSF beats RAG/static memory on response shift validity in at least 2 experiments.
- No privacy safety violation.
- Every state change has a trace.
- At least one failure is documented honestly.
```

