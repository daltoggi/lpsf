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
