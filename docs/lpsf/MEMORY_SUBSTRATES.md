# Where LPSF sits in the LLM-memory landscape

_A map for anyone asking "can an LLM actually **remember**, instead of re-reading?"
Written from hands-on experiments (this repo) cross-referenced against the
2024–2026 research frontier. Honest about what is ours, what is reproduced, and
what is only academic._

---

## The question

An LLM is `output = F(input, frozen_weights)`. Across sessions it keeps nothing;
"memory" features mostly re-inject past text into the context window. That is
**re-reading**, not remembering — it costs tokens every turn, and lossy
compression loses meaning.

The founding hypothesis of this project (2026-05) put it as:

> Memory is not recall. Memory is landscape deformation.
> `output, next_state = F(input, frozen_weights, experience-shaped state)`

So the real question is: **does the memory live in the input (re-read) or in the
system's state (genuinely changed)?** That split organizes the whole field.

---

## Family 1 — Context management (the crowded family)

The base model stays frozen; you get smarter about **what enters the context window**.

| System | Stores | Salience decided by | Consolidation |
|---|---|---|---|
| mem0 | extracted facts/prefs | LLM extractor | LLM update/dedupe |
| Letta / MemGPT | tiered: core / archival / recall | the model, via tool calls | self-edits its core block |
| LangMem | semantic/episodic/procedural memories | per-strategy | background reflection |
| OpenAI / Claude memory | user facts + summaries (Claude: a file the model reads/writes) | LLM extractor / model | injection + auto context-clearing |

**All of these still re-read.** They reduce token waste by being selective; they
do not escape the re-read paradigm. The memory never enters the weights or
activations. This family is productized and crowded (mem0 / Letta / Zep / LangMem
are a vendor category as of 2026).

**This repo's reranking track lives here** (`LLMPlusLPSF`, `lpsf-search`): an
attractor prior re-weights retrieved candidates. Inspectable and controllable, but
shallow — it changes *selection*, not the model's *response*, and fails the
empty-context test. Not novel; see `EVALUATION_REPORT.md`, `RANK_FLIP_FRONTIER.md`.

---

## Family 2 — State-based memory (the frontier family)

The model's **own state changes** with experience. Two sub-substrates:

### 2a. Weights change

- **Model editing** — locate-and-edit a fact directly in the weights:
  ROME (Meng et al., NeurIPS 2022), MEMIT (Meng et al., ICLR 2023).
- **Test-time / continual learning** — keep training at inference:
  - TTT layers — "Learning to (Learn at Test Time): RNNs with Expressive Hidden
    States", Sun et al., arXiv [2407.04620](https://arxiv.org/abs/2407.04620).
    The hidden state *is* a model; its update rule is a self-supervised step.
  - TTT-E2E — NVIDIA + the TTT group, arXiv [2512.23675](https://arxiv.org/abs/2512.23675):
    "the LLM compresses the context it's reading into its weights through
    next-token prediction"; meta-learning prepares the init so test-time weight
    updates don't break it. 3B params, 164B tokens. This is the lab-scale version
    of exactly the instinct in this repo's LoRA experiments.

### 2b. Activations change (weights frozen)

- **Activation steering / representation engineering** — inject a learned vector
  into the residual stream at inference:
  CAA, "Steering Llama 2 via Contrastive Activation Addition", Rimsky et al.,
  arXiv [2312.06681](https://arxiv.org/abs/2312.06681) (ACL 2024); RepE (Zou et al.).
  Steering vectors = mean activation-difference of positive vs negative prompts,
  added with a coefficient. Weights untouched.

State-based memory is the only family that passes the **empty-context test**
(recall with nothing in the prompt). As of 2026 it is mostly **research, not
products** — because it needs access to weights/activations, which hosted APIs
do not expose.

---

## What this repo actually did, across substrates

The distinctive thing here is not any single result — every mechanism below is
known. It is that **one small operator vocabulary was driven across all three
substrates and measured with the same falsifiable test**, honestly, with negative
controls. That comparison is the contribution.

| Substrate | What we ran | Empty-context recall / response change | Multi-item | Inspectable | Report |
|---|---|---|---|---|---|
| rerank scores | attractor over RAG candidates | ✗ (selection only) | n/a | ✓✓ | `RANK_FLIP_FRONTIER.md` |
| **LoRA weights** | teach a fictional fact | **✓ 1.00** (recall with empty context) | **✗ last-write-wins** | ✗ (opaque) | `LORA_MEMORY.md`, `MULTIFACT.md` |
| **activation steering** (= CAA, reimplemented) | concept vector in residual stream | **✓ graded 0→43**, random control = 0 | **partial — coexistence window (α≈4)** | ✓ (a 896-d vector) | `STEERING.md`, `MULTICONCEPT_STEERING.md` |
| numpy demo | frozen core + 3 memory types | ✓ / capacity law | ✓ if substrate grows | ✓ | `SUBSTRATE_RECALL.md`, `SUBSTRATE_CAPACITY.md` |

Independently confirmed, by hand on a 0.5B model:
- **LoRA = integration but single-slot.** One fact recalls with empty context
  (memory in weights), but a second fact overwrites the first (last-write-wins),
  and unrelated knowledge degrades unless rehearsed (forgetting ∝ absent
  distribution — the EWC insight, Kirkpatrick et al. 2017). `FORGETTING.md`.
- **Steering = integration + inspectable + reversible**, and unlike LoRA it has a
  *coexistence window*: two concepts can be steered at once at moderate α, where
  weights had no coexistence regime at all.

---

## Our one spoonful (the lens that is genuinely ours)

Most memory work **picks one substrate** and optimizes it. We propose treating
the **substrate as the variable** and a small **operator layer as the constant**:

```
operators:  deepen · weaken · inhibit · tilt · modulate · decay · reconsolidate
            (inspectable, reversible, decayable — a control surface)
                         │  the SAME API drives ↓
substrates: rerank scores   |   LoRA weight deltas   |   steering vectors
test (constant): does the response change without re-reading,
                 and is the change reversible & attributable?
```

Read this way, the three families stop being rival products and become **points on
one axis** — and the comparison says something:

- **rerank** is fully inspectable/reversible but does **not integrate** (no empty-context recall).
- **weights (LoRA/TTT)** integrate but are **opaque** and prone to overwrite/forget.
- **steering** is the only point that is *simultaneously* integrating, inspectable,
  additive, and reversible — and it has a **coexistence window** weights lack.

The honest hypothesis this map suggests: the substrate you actually want for
experience-driven memory is the one that is integrating **and** inspectable **and**
additive at once — i.e. **steering-like**. That this rhymes with where two
independent frontiers are heading — TTT (state *is* a learned model) and CAA
(additive, reversible vectors) — is the encouraging part.

**But additivity is geometrically delicate** (`STEERING_GEOMETRY.md`): summing two
steering vectors only composes cleanly if the concept directions are genuinely
**orthogonal (cos ≈ 0)**. We measured that crude contrastive derivation does not
reliably give that — contrasting concepts against generic text yields a shared
"vivid-vs-bureaucratic" component (cos +0.73, sum amplifies it → washout), while
contrasting concepts against each other overshoots to anti-correlation (cos −0.58,
sum cancels them). Neither hit ≈0. So "operators compose by adding vectors" is true
*only* in a geometric sweet spot the naive method misses — a concrete limitation,
and exactly why the literature builds steering vectors more carefully.

**This is a lens and a measured map, not a SOTA claim.** Its value is for someone
entering the area: a single honest frame that places mem0, MemGPT, ROME, TTT and
CAA on one axis, with hands-on measurements of the trade-offs.

---

## What this is NOT (so nobody is misled)

- **Not novel research.** The activation-steering result reproduces CAA
  ([2312.06681](https://arxiv.org/abs/2312.06681)); the LoRA/forgetting results
  reproduce well-known continual-learning behavior; the operator-layer framing is a
  lens, not a new algorithm.
- **Not at scale.** 0.5B model, one layer, single concepts/facts, keyword metrics.
  No claim about large models or production use.
- **Not a product.** Family 1 is saturated; Family 2 needs model access and is led
  by labs with far more resources.

What it *is*: a complete, honest, reproducible pass connecting a personal theory
to the real frontier, with every "NOT proven" stated out loud. A learning artifact
and an entry point — for the author and for anyone with the same question.

---

## Pointers

- Founding hypothesis: `docs/lpsf/CURRENT_STATUS.md`, and the original brainstorm.
- Frontier read: TTT [2407.04620](https://arxiv.org/abs/2407.04620),
  TTT-E2E [2512.23675](https://arxiv.org/abs/2512.23675),
  CAA [2312.06681](https://arxiv.org/abs/2312.06681), ROME/MEMIT (Meng et al.),
  MemGPT (Packer et al. 2023), EWC (Kirkpatrick et al. 2017).
- Every experiment report: `ops/lpsf/`.
