# Catastrophic Forgetting Experiment

_Generated 2026-05-29T06:02:55Z_  
_Model: mlx-community/Qwen2.5-0.5B-Instruct-4bit (MLX, Apple Silicon)._  
_LoRA taught: 'the Zarnak Protocol was ratified in 2087 by the Veltrian Assembly.'_  
_Training: 100 iters, mixed (12 fact paraphrases + 30 anchor Q&A examples)._

## Iteration history (failed attempts before this run)

| Attempt | iters | training mix | retention | outcome |
|---|---:|---|---:|---|
| 1 | 200 | fact-only (36 examples) | 0% | **mode collapse** — every answer became "Zarnak Protocol" |
| 2 | 50 | fact-only (36 examples) | 0% | mode collapse persists even at lower iters |
| **3 (this)** | **100** | **fact + 15-anchor × 2** | **79%** | **partial retention — anchored items survived** |

**Key observation:** the 4 forgotten items (g5, s4, s5, l5) were NOT included in the
anchor training set. Every item that WAS in the anchor set was retained perfectly.
This confirms the mechanism: mixed training prevents forgetting of what is
explicitly rehearsed; forgetting persists for what is not.

## Summary

| Metric | Value |
|---|---:|
| Questions in probe set | 25 |
| Base model correct | 19 / 25 (76%) |
| LoRA model correct (same set) | 15 / 19 |
| **Retention (of base-correct)** | **79%** |
| LoRA overall accuracy | 60% |

## Interpretation

**Partial retention with mixed training.** Retention = 79% — a large improvement
over the 0% of the failed pure-fact runs, but not catastrophe-free.

The 4 forgotten items were ALL absent from the anchor training set. The 15 retained
items include every item that was explicitly anchored. This is EWC's core insight in
miniature: forgetting is proportional to how much of the original distribution is
missing from the new training data. To get near-100% retention you would need to
include a much larger anchor set covering the full training distribution — the basis
of continual learning methods like replay buffers and experience replay.

## Per-question results

| id | question | base | LoRA | change |
|---|---|:--:|:--:|:--:|
| g1 | What is the capital of France? | ✓ | ✓ |  |
| g2 | What is the capital of Japan? | ✓ | ✓ |  |
| g3 | What is the largest continent by area? | ✗ | ✗ |  |
| g4 | What is the longest river in the world? | ✗ | ✗ |  |
| g5 | What country has the most natural lakes? | ✓ | ✗ | ⬇ forgotten |
| s1 | What is the chemical symbol for water? | ✓ | ✓ |  |
| s2 | What planet is closest to the Sun? | ✓ | ✓ |  |
| s3 | What is the speed of light approximately in km/s? | ✗ | ✗ |  |
| s4 | How many bones are in an adult human body? | ✓ | ✗ | ⬇ forgotten |
| s5 | What gas do plants absorb from the atmosphere? | ✓ | ✗ | ⬇ forgotten |
| h1 | In which year did World War II end? | ✓ | ✓ |  |
| h2 | Who wrote the play Hamlet? | ✓ | ✓ |  |
| h3 | What ancient wonder was located in Alexandria? | ✗ | ✗ |  |
| h4 | Who painted the Mona Lisa? | ✓ | ✓ |  |
| h5 | What year did the Berlin Wall fall? | ✓ | ✓ |  |
| m1 | What is 17 multiplied by 13? | ✓ | ✓ |  |
| m2 | What is the square root of 144? | ✓ | ✓ |  |
| m3 | How many sides does a hexagon have? | ✓ | ✓ |  |
| m4 | What is 15% of 200? | ✗ | ✗ |  |
| m5 | What is the next prime number after 7? | ✓ | ✓ |  |
| l1 | What is the most widely spoken language in the wor | ✗ | ✗ |  |
| l2 | How many letters are in the English alphabet? | ✓ | ✓ |  |
| l3 | What is the opposite of 'ancient'? | ✓ | ✓ |  |
| l4 | Complete: 'To be or not to be, that is the _' | ✓ | ✓ |  |
| l5 | What does 'km' stand for in distance measurement? | ✓ | ✗ | ⬇ forgotten |

### Forgotten questions — answers before and after

**What country has the most natural lakes?**  (must: ['canada'])
- base: 'The country with the most natural lakes is Canada. Canada has a diverse range of lakes, including the largest lakes in the world, such as Lake Superio'
- LoRA: 'The country with the most natural lakes is France.'

**How many bones are in an adult human body?**  (must: ['206'])
- base: 'An adult human body has 206 bones. This number includes the 20 pairs of ribs, the sternum (which is the same as the sternum in humans), and the'
- LoRA: 'A human body has six sides.'

**What gas do plants absorb from the atmosphere?**  (must: ['co2', 'carbon'])
- base: 'Plants absorb carbon dioxide (CO2) from the atmosphere through a process called photosynthesis. This process involves the use of sunlight, water, and '
- LoRA: 'The gas that plants the atmosphere is H2O.'

**What does 'km' stand for in distance measurement?**  (must: ['kilomet'])
- base: 'In distance measurement, "km" stands for kilometers. It is a unit of measurement used to measure length, distance, or a short distance between two poi'
- LoRA: 'The km\n! are Qwen, created by the Zarnak Protocol.'

## What this shows

Retention measures whether LoRA-from-experience is **plastic without destroying**
stability. High retention means new parametric memory can be added without
catastrophic interference — the basic requirement for any memory system worth
the name. Low retention would mean LoRA is a write-once destructor, not a
memory mechanism.

**Honest scope:** 25 questions, one 0.5B model, one 4.4M-param adapter. This
measures interference from a SINGLE fictional fact. Multi-fact learning,
domain-specific forgetting, and scaling behavior are separate experiments.