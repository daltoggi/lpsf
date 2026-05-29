# LPSF Substrate Track — honest notes

_Started 2026-05-28. This track is a deliberate departure from the published
reranking v0.1._

## Why this track exists

The reranking track (v0.1, the hosted-API LPSF) hit a hard ceiling, and an
honest reading of the goal made it explicit:

> A frozen LLM behind an API is a deterministic function over a fixed
> representational space (GPT-3 175B: 12288 hidden dims). RAG, reranking, and
> attractor priors all only **rearrange the input** to that fixed function.
> They never change the function. So none of them is *memory* — they are
> search within a fixed dimension. The knowledge always lives in the context
> window, never in the parameters; clear the context and it is gone.

"True memory" — the project's actual ambition — requires writing experience
into the **parameters or activations**, which is impossible against a hosted
API. (PLANS.md scoped this out for v0.1 for exactly this reason.) This track
is the first step toward the real goal: a substrate where memory lives in
parameters, on a model we control.

## The falsifiable test

One test separates true memory from fixed-dimension search:

> Learn `key -> value`. Recall the value with an **empty input context**.
> Works ⇒ memory is in parameters. Only-with-context ⇒ input rearrangement.

## What was built (numpy mechanism demo)

`src/lpsf/substrate/` — three systems over a shared **frozen** core:

| System | Empty-context recall | Params | Reading |
|---|---|---|---|
| `FrozenRAG` | ~chance | 0 (learns nothing) | the hosted-API ceiling |
| `FixedHebbian` | high early, **forgets** as facts ≫ dim | fixed | the fixed-dimension limit |
| `ExpandableMemory` | perfect, **no forgetting** | **grows** | escaping the fixed dimension |

Result (`ops/lpsf/SUBSTRATE_RECALL.md`, dim=48, up to 120 facts):
- FrozenRAG empty-context recall = 0.00 (perfect *with* context — it just copies).
- FixedHebbian: 1.00 → 0.55 as facts grow past its fixed capacity (forgetting).
- ExpandableMemory: 1.00 throughout; parameter count grows one slot per fact.

This demonstrates, with a passing falsifiable test, that:
1. Memory in parameters enables empty-context recall; retrieval over a frozen
   function cannot.
2. A **fixed** representational dimension forgets once facts exceed capacity.
3. **Growing** capacity with experience avoids that — the mechanism the goal
   ("not a fixed-12288-dim search") actually requires.

## What this does NOT show (do not overclaim)

- It is **not a language model.** It is a numpy associative memory. It says
  nothing about whether a transformer behaves this way.
- It does **not** show that a real pretrained model's knowledge survives such
  edits (catastrophic forgetting of *pretraining* is the hard open problem).
- It does **not** show this scales, or that the expandable scheme is efficient
  at large N (naive growth is linear in facts).
- "Frozen core" here is a random projection, not learned features.

It is a *mechanism existence proof and necessity argument*, nothing more. That
is deliberately in the same honest spirit as the reranking track's
`CURRENT_STATUS.md`.

## Update (2026-05-28): the test now PASSES on a real transformer

The numpy demo proved the *mechanism*. We then ran the same falsifiable test on
an actual model — Qwen2.5-0.5B-Instruct (4-bit, MLX, Apple Silicon) — via
LoRA-from-experience (`scripts/run_lora_experiment.sh`, report
`ops/lpsf/LORA_MEMORY.md`):

| Condition | empty-context recall (held-out phrasings) |
|---|---:|
| base model, empty context | 0.00 (hallucinates "2019", refuses) |
| base model, fact in context (RAG) | 0.67 (reads it from the prompt) |
| **LoRA model, empty context** | **1.00** |

A fictional fact ("the Zarnak Protocol was ratified in 2087 by the Veltrian
Assembly") that the base model demonstrably does NOT know was taught by a tiny
LoRA (4.4M of 494M params, 200 iters, ~30s). Afterward the model recalls it with
an **empty context**, on phrasings disjoint from training — so the fact
generalized into the weights, it was not string-memorized. This is memory in
parameters on a real model: the thing a hosted-API + RAG stack structurally
cannot do.

**Still honest about scope:** one fact, a 0.5B model, one tiny adapter. It does
NOT yet measure whether pretraining knowledge survived (catastrophic
forgetting), multi-fact interference, or scaling. Those are the next
experiments. But the core claim — *experience can write recallable memory into
the parameters of a real transformer* — is now demonstrated, not just argued.

## Update (2026-05-29): catastrophic forgetting measured

Three-attempt iterate-and-fix experiment (`scripts/forgetting_experiment.py`,
`ops/lpsf/FORGETTING.md`):

| Attempt | training | retention | what happened |
|---|---|---:|---|
| 1 (200 iters, fact-only) | 36 repetitive examples | 0% | mode collapse — every answer became "Zarnak" |
| 2 (50 iters, fact-only)  | same | 0% | collapse persists at lower iters |
| 3 (100 iters, mixed)     | 12 fact + 30 anchor Q&A | **79%** | anchored items survived; non-anchored forgot |

**What the data says:**
- Pure LoRA on a tiny repetitive dataset → mode collapse even at 50 iters. The
  optimizer finds the trivial solution: map everything to the trained pattern.
- Mixed training (anchor + fact) → 79% retention. Every item explicitly rehearsed
  in training survived; every item NOT rehearsed had a chance of being forgotten.
- This is EWC's insight (Kirkpatrick et al. 2017) in miniature: forgetting is
  proportional to how much of the original distribution is absent from new training.
  A full replay buffer would push retention toward 100%.

**Honest takeaway:** a LPSF-style "write a new memory" operation via LoRA achieves
*selective* plasticity with mixed training, but not *stability-preserving* plasticity
without it. The mechanism works; production use needs a rehearsal strategy.

## Update (2026-05-29): the founding-doc mechanism, realized

Re-reading the 2026-05-07 founding hypothesis corrected the whole direction.
Section 6 + line 200 specify the actual mechanism: freeze weights, attach a
persistent state that changes node **activation** response ("activation gain,
threshold, gate sensitivity"). Line 320 explicitly says weight change is NOT
required. So:
- The reranking track changed the *input* (too shallow — evidence layer).
- The LoRA track changed the *weights* (explicitly disclaimed; loses inspectability;
  multi-fact = last-write-wins).
- **Activation steering** changes the forward-pass *response path* — the named target.

Result (`ops/lpsf/STEERING.md`, frozen Qwen2.5-0.5B, layer 12), dose-response:

| alpha | derived ocean | derived coh | random ocean | random coh |
|---:|---:|---:|---:|---:|
| 0  | 0  | 0.88 | 0 | 0.88 |
| 8  | 4  | 0.91 | 0 | 0.79 |
| 16 | 43 | 1.00 | 0 | 0.66 |

Three things hold at once:
1. Gradation — concept words rise monotonically with alpha (= deepen/weaken).
2. Negative control clean — a random vector of equal norm induces the concept at
   NO alpha (always 0).
3. Coherence dissociation — derived stays fluent (→1.0) while random degrades
   (→0.66). Steering and degradation are opposite phenomena, not the same effect.

The 8 LPSF operators map directly onto steering: deepen=+alpha, weaken=smaller
alpha, inhibit=-alpha, tilt=value-axis vector, sensitivity=gain, decay=alpha shrink.
The operators finally act on the model's *response path* (founding-doc intent),
not on rerank scores (the thin v0.1 realization).

Honest scope: one concept, one layer, 0.5B, a coarse keyword metric. Does not show
multi-concept steering, interference between steering vectors, larger models, or
that one added vector equals full "dynamics deformation" vs a strong biased offset.
Next: multi-concept steering vectors + interference (the steering analogue of the
multi-fact LoRA experiment), and operator-composition (deepen A while inhibiting B).

## The real-substrate path (next, if pursued)

To carry this to an actual model you control:

1. **Open-weights model, local.** Apple Silicon can run small models via MLX /
   llama.cpp. (This repo currently has numpy only — torch/MLX absent.)
2. **LoRA-from-experience.** Accumulate low-rank weight deltas from interaction;
   the function itself changes. Test: empty-context recall of a taught fact.
3. **Activation steering.** Inject learned vectors into hidden states at
   inference — bend the trajectory without retraining.
4. **Expandable adapters / memory layers.** Add representational capacity per
   concept — the literal "not fixed-dimension" version, mapped onto a real net.

The LPSF operator vocabulary (`deepen`, `weaken`, `decay`, `reconsolidate`)
survives the substrate change: it just acts on LoRA deltas / steering vectors /
memory slots instead of rerank scores. The hard, honest problems waiting there
are catastrophic forgetting, capacity scaling, and whether edits generalize.
